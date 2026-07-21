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
	FString ServerTimestampIso;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	bool IsLive = false; // intentionally not bIsLive because it differentiates between unreal setting the state and it must share the naming with the C# DTO

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather Data")
	float SunAlpha = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	FString TimeIso = "";

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	float TempC = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather Data")
	float WindSpeed = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	int32 CloudsPercent = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	int32 WeatherStateId = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Weather Data")
	float UpdateIntervalTime = 0.0f;

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

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Control Data")
	bool bIsLive;

	UFUNCTION(BlueprintImplementableEvent, Category = "Weather Data|UI")
	void OnToggleIsLive(bool bIsLiveState);

	float CalculateSecondsUntilNextServerUpdate(const FString& ServerTimeIso, const float UpdateInterval);

	FTimerHandle ServerPollingTimerHandle;
	FTimerHandle ConnectionCheckTimerHandle;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weather Data|Network", meta = (ClampMin = "1.0"))
	float PollingIntervalLive = 5.0f; // Default, is dynamic based on ScheduleNextWeatherCheckLive

	int32 ServerConnectionMaxRetries = 3;
	int32 ServerConnectionCurrentRetries = 3;

	// How fast to retry after a failure to get newest data.
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weather Data|Network")
	float PacketRetryInterval = 3.3f;

	// Schedules the delay between polling for live packets
	void ScheduleNextWeatherCheckLive(const float SecondsTillNextExpected);

	void StartConnectionCheck();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather Data")
	int32 HighestId = 1;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather Data")
	int32 HistoricIdRequested = 1;

	UFUNCTION(BlueprintImplementableEvent, Category = "Weather Data|UI")
	void OnHistoricIdRequest(int32 NewHistoricIdRequested);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather Data")
	int32 HistoricIdCurrent = 1;

	UFUNCTION(BlueprintCallable, Category = "Weather Network")
	void FetchWeather(int32 TargetId = 0);

	void OnWeatherResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather Data")
	FWeatherPacket LastWeatherPacket;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather Data")
	FWeatherPacket CurrentWeather;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather Data")
	FWeatherPacket HistoricalWeather;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather Data")
	FWeatherPacket TargetWeather;

	UFUNCTION(BlueprintImplementableEvent, Category = "Weather Data|UI")
	void OnTargetWeatherChanged(const FWeatherPacket& NewTargetWeather);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weather Data")
	FWeatherPacket DisplayWeather;

	UFUNCTION(BlueprintCallable, Category = "Weather Machine")
	void SetLiveState(bool bWantsToBeLive);

	UFUNCTION(BlueprintCallable, Category = "Weather Machine")
	void ShiftHistoricId(int32 IdDelta);

	FTimerHandle NetworkDebounceTimerHandle;

	void TriggerHistoricNetworkRequest();

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

};
