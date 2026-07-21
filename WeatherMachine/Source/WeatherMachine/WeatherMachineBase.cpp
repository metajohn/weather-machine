// Fill out your copyright notice in the Description page of Project Settings.


#include "WeatherMachineBase.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "JsonUtilities.h"
#include "Net/UnrealNetwork.h"

// Sets default values
AWeatherMachineBase::AWeatherMachineBase()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

}

// Called when the game starts or when spawned
void AWeatherMachineBase::BeginPlay()
{
	Super::BeginPlay();

	SetLiveState(true);
	FetchWeather();
}

float AWeatherMachineBase::CalculateSecondsUntilNextServerUpdate(const FString& ServerTimeIso, const float UpdateInterval)
{
	FDateTime ServerTime = FDateTime::ParseIso8601(*ServerTimeIso, ServerTime);

	UE_LOG(LogTemp, Log, TEXT("Received Server Time ISO %s from last live update."), *ServerTimeIso);

	// If parsing fails, fall back to the raw UpdateInterval provided by the server
	if (ServerTime == FDateTime::MinValue())
	{
		UE_LOG(LogTemp, Warning, TEXT("Failed to parse ISO string: %s. Falling back to UpdateInterval."), *ServerTimeIso);
		return UpdateInterval;
	}

	// 2. Calculate next expected update using the server's UpdateInterval (in seconds)
	FDateTime NextExpectedUpdate = ServerTime + FTimespan::FromSeconds(UpdateInterval);

	// 3. Compare against current client UTC time
	FDateTime CurrentUtcTime = FDateTime::UtcNow();
	FTimespan TimeRemaining = NextExpectedUpdate - CurrentUtcTime;

	float RemainingSeconds = TimeRemaining.GetTotalSeconds();

	// Add a 5-second buffer to ensure the Azure job finishes writing before we check
	float BufferSeconds = 5.0f;
	float FinalInterval = RemainingSeconds + BufferSeconds;


	
	// If the expected time has already passed, return the standard wait time
	return (FinalInterval > 0.0f) ? FinalInterval : UpdateInterval;
}

void AWeatherMachineBase::ScheduleNextWeatherCheckLive(const float SecondsTillNextExpected)
{
	UE_LOG(LogTemp, Log, TEXT("Next Weather Check Scheduled in  %f seconds."), SecondsTillNextExpected);

	GetWorldTimerManager().ClearTimer(ServerPollingTimerHandle);

	GetWorldTimerManager().SetTimer(
		ServerPollingTimerHandle,
		[this]()
		{
			this->FetchWeather();
		},
		SecondsTillNextExpected,
		false
	);
}

void AWeatherMachineBase::StartConnectionCheck()
{
	if (ServerConnectionCurrentRetries <= 0)
	{
		UE_LOG(LogTemp, Error, TEXT("Connection To Server Lost"));
		return;
	}
	ServerConnectionCurrentRetries--;
	UE_LOG(LogTemp, Error, TEXT("Checking Connection to Server, %d Attempts remain"), ServerConnectionCurrentRetries);
	GetWorldTimerManager().ClearTimer(ConnectionCheckTimerHandle);
	GetWorldTimerManager().SetTimer(
		ConnectionCheckTimerHandle,
		[this]()
		{
			this->FetchWeather();
		},
		PacketRetryInterval,
		false
	);
}

void AWeatherMachineBase::FetchWeather(int32 TargetId)
{
	FString BaseURL = TEXT("http://localhost:7071/api/weather"); // temporary to local testing

	// TODO complete testing and implementation of implicit TargetId, to allow timers to retry
	if (TargetId > 0)
	{
		TargetId = HistoricIdRequested;
		BaseURL = FString::Printf(TEXT("%s?id=%d"), *BaseURL, TargetId);

		UE_LOG(LogTemp, Log, TEXT("FetchWeather: Requesting historic frame ID: %d"), TargetId);
	}
	else
	{
		TargetId = 0;
		UE_LOG(LogTemp, Log, TEXT("FetchWeather: Requesting latest live weather data..."));
	}

	// Create request
	FHttpRequestRef Request = FHttpModule::Get().CreateRequest();

	// Bind request to response event
	Request->OnProcessRequestComplete().BindUObject(this, &AWeatherMachineBase::OnWeatherResponseReceived);

	// Define request members
	Request->SetURL(BaseURL);
	Request->SetVerb(TEXT("GET"));
	Request->SetHeader(TEXT("User-Agent"), TEXT("X-UnrealEngine-Agent"));
	Request->SetHeader(TEXT("Accept"), TEXT("application/json"));

	// Send Request
	Request->ProcessRequest();
}

void AWeatherMachineBase::OnWeatherResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
	// network not available
	if (!bWasSuccessful || !Response.IsValid())
	{
		UE_LOG(LogTemp, Warning, TEXT("Weather request failed: Network unreachable."))
		return;
	}

	// returned NOT 200
	if (Response->GetResponseCode() != 200)
	{
		UE_LOG(LogTemp, Warning, TEXT("Weather request returned server error code: %d"), Response->GetResponseCode());
		return;
	}

	FString JsonString = Response->GetContentAsString();

	UE_LOG(LogTemp, Log, TEXT("RAW SERVER RESPONSE: %s"), *JsonString);

	if (FJsonObjectConverter::JsonObjectStringToUStruct(JsonString, &LastWeatherPacket, 0, 0))
	{
		//if (FJsonObjectConverter::JsonObjectStringToUStruct(JsonString, &LastWeatherPacket, 0, 0))
		//{
		//	UE_LOG(LogTemp, Log, TEXT("=================================================="));
		//	UE_LOG(LogTemp, Log, TEXT("   WEATHER STRUCT VALIDATION READOUT"));
		//	UE_LOG(LogTemp, Log, TEXT("=================================================="));
		//	UE_LOG(LogTemp, Log, TEXT("Id:                     %d"), LastWeatherPacket.Id);
		//	UE_LOG(LogTemp, Log, TEXT("ServerTimestampIso:     %.2f"), LastWeatherPacket.ServerTimestampIso);
		//	UE_LOG(LogTemp, Log, TEXT("bIsLive:                %s"), LastWeatherPacket.IsLive ? TEXT("True") : TEXT("False"));
		//	UE_LOG(LogTemp, Log, TEXT("SunAlpha:               %.4f"), LastWeatherPacket.SunAlpha);
		//	UE_LOG(LogTemp, Log, TEXT("UpdateIntervalTime:     %.2f"), LastWeatherPacket.UpdateIntervalTime);
		//	UE_LOG(LogTemp, Log, TEXT("TimeIso:                %s"), *LastWeatherPacket.TimeIso);
		//	UE_LOG(LogTemp, Log, TEXT("TempC:                  %.2f"), LastWeatherPacket.TempC);
		//	UE_LOG(LogTemp, Log, TEXT("WindSpeed:              %.2f"), LastWeatherPacket.WindSpeed);
		//	UE_LOG(LogTemp, Log, TEXT("CloudsPercent:          %d"), LastWeatherPacket.CloudsPercent);
		//	UE_LOG(LogTemp, Log, TEXT("WeatherStateId:         %d"), LastWeatherPacket.WeatherStateId);
		//	UE_LOG(LogTemp, Log, TEXT("=================================================="));
		//}

		if (LastWeatherPacket.IsLive)
		{
			UE_LOG(LogTemp, Log, TEXT("Processing live data packet for Id: %d"), LastWeatherPacket.Id);

			// we received a live packet that is not new
			if (CurrentWeather.Id >= LastWeatherPacket.Id && CurrentWeather.Id != 0) // CurrentWeather.Id != is our cold start boolean check
			{
				// if their isnt a current connection check start a new one
				if (!ConnectionCheckTimerHandle.IsValid())
				{
					ServerConnectionCurrentRetries = ServerConnectionMaxRetries;
					StartConnectionCheck();
				}
			}
			// we received a fresh live packet
			else
			{
				GetWorldTimerManager().ClearTimer(ConnectionCheckTimerHandle);

				CurrentWeather = LastWeatherPacket;
				UE_LOG(LogTemp, Log, TEXT("LiveWeather Updated, set Highest Id - Highest Id: %d"), HighestId);
				HighestId = LastWeatherPacket.Id;

				// we are live, update with the fresh packet
				if (bIsLive)
				{
					TargetWeather = CurrentWeather;
					UE_LOG(LogTemp, Log, TEXT("SunAlpha on TargetWeather %.4f"), TargetWeather.SunAlpha)
					HistoricIdCurrent = HighestId;
					HistoricIdRequested = HistoricIdCurrent;
					OnHistoricIdRequest(HistoricIdRequested);
					OnTargetWeatherChanged(TargetWeather);
				}

				float TimeTillNextUpdate = CalculateSecondsUntilNextServerUpdate(CurrentWeather.ServerTimestampIso, CurrentWeather.UpdateIntervalTime);
				ScheduleNextWeatherCheckLive(TimeTillNextUpdate);
			}
		}
		// we are historic and we got the packet we wanted
		else if (!LastWeatherPacket.IsLive && LastWeatherPacket.Id == HistoricIdRequested)
		{
			GetWorldTimerManager().ClearTimer(ConnectionCheckTimerHandle);

			UE_LOG(LogTemp, Log, TEXT("Processing historic data packet for Id %d."), LastWeatherPacket.Id)
			HistoricalWeather = LastWeatherPacket;
			TargetWeather = HistoricalWeather;
			HistoricIdCurrent = HistoricIdRequested;
			OnTargetWeatherChanged(TargetWeather);
		}
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to parse JSON string into FWeatherPacket struct. Schema mismatch"));
		return;
	}
}

void AWeatherMachineBase::SetLiveState(bool bWantsToBeLive)
{
	bIsLive = bWantsToBeLive;

	if (bIsLive)
	{
		UE_LOG(LogTemp, Log, TEXT("Weather Machine: LIVE"));
		OnToggleIsLive(bIsLive);

		// set TargetWeather to cached CurrentWeather
		TargetWeather = CurrentWeather;
		HistoricIdCurrent = CurrentWeather.Id;
		HistoricIdRequested = HistoricIdCurrent;
		OnHistoricIdRequest(HistoricIdRequested);
		OnTargetWeatherChanged(TargetWeather);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Weather Machine: HISTORIC"));
		OnToggleIsLive(bIsLive);
	}
}

void AWeatherMachineBase::ShiftHistoricId(int32 IdDelta)
{
	if (bIsLive)
	{
		UE_LOG(LogTemp, Log, TEXT("Shift Historic Frame Returned because Is Live"));
		return;
	}
	int32 TargetId = HistoricIdRequested + IdDelta;

	if (TargetId < 1)
	{
		TargetId = 1;
	}
	else if (TargetId > HighestId)
	{
		TargetId = HighestId;
	}
	UE_LOG(LogTemp, Log, TEXT("Processing frame shift"));
	if (TargetId != HistoricIdRequested)
	{
		HistoricIdRequested = TargetId;
		OnHistoricIdRequest(HistoricIdRequested);

		GetWorldTimerManager().ClearTimer(NetworkDebounceTimerHandle);

		// debounce the network request.
		GetWorldTimerManager().SetTimer(
			NetworkDebounceTimerHandle,
			this,
			&AWeatherMachineBase::TriggerHistoricNetworkRequest,
			0.2f, // Delay in seconds (500ms)
			false  // Do NOT loop
		);
	}
}

void AWeatherMachineBase::TriggerHistoricNetworkRequest()
{
	if(!bIsLive)
	{
		FetchWeather(HistoricIdRequested);
		UE_LOG(LogTemp, Log, TEXT("Requested ID changed to: %d. Fetching Historic Record"), HistoricIdRequested);

		if (!ConnectionCheckTimerHandle.IsValid())
		{
			ServerConnectionCurrentRetries = ServerConnectionMaxRetries;
			StartConnectionCheck();
		}
	}
}

// Called every frame
void AWeatherMachineBase::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

}

