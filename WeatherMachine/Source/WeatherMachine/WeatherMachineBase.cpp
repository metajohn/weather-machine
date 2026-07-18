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

void AWeatherMachineBase::FetchWeather(int32 TargetId)
{
	FString BaseURL = TEXT("http://localhost:7071/api/weather");

	if (TargetId > 0)
	{
		BaseURL = FString::Printf(TEXT("%s?id=%d"), *BaseURL, TargetId);

		UE_LOG(LogTemp, Log, TEXT("FetchWeather: Requesting historic frame ID: %d"), TargetId);
	}
	else
	{
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
			CurrentWeather = LastWeatherPacket;
			UE_LOG(LogTemp, Log, TEXT("SunAlpha on CurrentWeather %.4f"), CurrentWeather.SunAlpha)


			if (bIsLive)
			{
				TargetWeather = CurrentWeather;
				OnTargetWeatherChanged(TargetWeather);
				UE_LOG(LogTemp, Log, TEXT("SunAlpha on TargetWeather %.4f"), TargetWeather.SunAlpha)
				UE_LOG(LogTemp, Log, TEXT("CurrentWeather Updated, set Highest Id - Highest Id: %d"), HighestId);
				HighestId = LastWeatherPacket.Id;
				HistoricIdRequested = HighestId;
			}

		}
		else if (!LastWeatherPacket.IsLive && LastWeatherPacket.Id == HistoricIdRequested)
		{
			UE_LOG(LogTemp, Log, TEXT("Processing historic data packet for Id %d."), LastWeatherPacket.Id)
			HistoricalWeather = LastWeatherPacket;
			TargetWeather = HistoricalWeather;
			OnTargetWeatherChanged(TargetWeather);
		}
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to parse JSON string into FWeatherPacket struct. Schema mismatch"));
	}
}

void AWeatherMachineBase::ToggleIsLive()
{
	SetLiveState(!bIsLive);
	
}

void AWeatherMachineBase::SetLiveState(bool bWantsToBeLive)
{
	bIsLive = bWantsToBeLive;

	if (bIsLive)
	{
		UE_LOG(LogTemp, Log, TEXT("Weather Machine: Switched to LIVE streaming. Resuming updates."));
		FetchWeather();
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Weather Machine: PAUSED live streaming. Clearing active timers."));
		// Clear the timer so no more background loops fire while paused
		/*GetWorldTimerManager().ClearTimer(WeatherTimerHandle);*/
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
		UE_LOG(LogTemp, Log, TEXT("Shift Historic Frame tried to go below 1"));
		TargetId = 1;
	}
	else if (TargetId > HighestId)
	{
		UE_LOG(LogTemp, Log, TEXT("Shift Historic Frame tried to go above highest value"));
		TargetId = HighestId;
	}
	UE_LOG(LogTemp, Log, TEXT("Processing frame shift"));
	if (TargetId != HistoricIdRequested)
	{
		HistoricIdRequested = TargetId;

		UE_LOG(LogTemp, Log, TEXT("Requested ID changed to: %d. Fetching Historic Record"), TargetId);
		FetchWeather(TargetId);
	}
}

// Called every frame
void AWeatherMachineBase::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

}

