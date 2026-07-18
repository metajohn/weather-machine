// Fill out your copyright notice in the Description page of Project Settings.


#include "WeatherMachineBase.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "JsonUtilities.h"

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

	FetchLatestWeather();	
}

void AWeatherMachineBase::FetchLatestWeather()
{
	// Create request
	FHttpRequestRef Request = FHttpModule::Get().CreateRequest();

	// Bind request to response event
	Request->OnProcessRequestComplete().BindUObject(this, &AWeatherMachineBase::OnWeatherResponseReceived);

	// Define request members
	Request->SetURL(TEXT("http://localhost:5000/api/weather"));
	Request->SetVerb(TEXT("GET"));
	Request->SetHeader(TEXT("User-Agent"), TEXT("X-UnrealEngine-Agent"));
	Request->SetHeader(TEXT("Accept"), TEXT("application/json"));

	// Send Request
	Request->ProcessRequest();
}

void AWeatherMachineBase::OnWeatherResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
	if (!bWasSuccessful || !Response.IsValid())
	{
		UE_LOG(LogTemp, Warning, TEXT("Weather request failed: Network unreachable."))
		return;
	}

	if (Response->GetResponseCode() != 200)
	{
		UE_LOG(LogTemp, Warning, TEXT("Weather request returned server error code: %d"), Response->GetResponseCode());
		return;
	}

	FString JsonString = Response->GetContentAsString();

	if (FJsonObjectConverter::JsonObjectStringToUStruct(JsonString, &CurrentWeather, 0, 0))
	{
		UE_LOG(LogTemp, Log, TEXT("Successfully mapped weather packet! IsLive: % s"), CurrentWeather.bIsLive ? TEXT("True") : TEXT("False"));

		if (CurrentWeather.bIsLive)
		{
			UE_LOG(LogTemp, Log, TEXT("Processing live data packet for Id: %d"), CurrentWeather.Id);
		}
		else
		{
			UE_LOG(LogTemp, Log, TEXT("Processing historic data packet for Id %d. Verification required."), CurrentWeather.Id)
		}
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to parse JSON string into FWeatherPacket struct. Schema mismatch"));
	}
}

// Called every frame
void AWeatherMachineBase::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

}

