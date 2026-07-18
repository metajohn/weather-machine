// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interfaces/IHttpRequest.h"
#include "WeatherMachineBase.generated.h"

USTRUCT(BlueprintType)
struct FWeatherPacket
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	int32 Id = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	bool bIsLive = false;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	float SunAlpha = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	float UpdateSpeed = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	FString TimeIso = "";

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	float TempC = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	float WindSpeed = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	int32 CloudsPercent = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	int32 WeatherState = 0;
};

UCLASS()
class WEATHERMACHINE_API AWeatherMachineBase : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AWeatherMachineBase();

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

	bool bIsLive;
	int32 HighestId;
	int32 HistoricIdRequested;

	UFUNCTION(BlueprintCallable, Category = "Weather Network")
	void FetchLatestWeather();

	void OnWeatherResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	FWeatherPacket CurrentWeather;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	FWeatherPacket HistoricalWeather;
public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

};
