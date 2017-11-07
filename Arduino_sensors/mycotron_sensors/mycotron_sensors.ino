/**************** Sensors Module V1.2 for Mushroom Project ***********************
Author:  ekulyyev: kea2288@yandex.ru
         username: email@address
         
Lisence: N/A

Note:    This piece of source code is supposed to be used as a demostration ONLY. More
         sophisticated calibration is required for industrial field application. 
         
                                                           Mycotronics    2017-10-31
************************************************************************************/

#include "DHT.h"
#include <math.h>

#define DHTPIN 2     // what pin we're connected to
#define DHTTYPE DHT22   // DHT 22  (AM2302)
#define CO2PIN A0

DHT dht(DHTPIN, DHTTYPE);
int val = 0;

void setup() 
{
	Serial.begin(9600);
    dht.begin();
}

void loop() 
{
	val = analogRead(CO2PIN);
    //float voltage = val * (5.0 / 1023.0);
	Serial.print("CO2: ");
    Serial.println(val);
    //Serial.println(voltage);

    // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
    float h = dht.readHumidity();
    float t = dht.readTemperature();

    // check if returns are valid, if they are NaN (not a number) then something went wrong!
    if (isnan(t) || isnan(h)) 
    {
        Serial.println("Humidity: Fail");
        Serial.println("Temperature: Fail");
    }
    else 
    {
        Serial.print("Humidity: ");
        Serial.println(h);
        Serial.print("Temperature: ");
        Serial.println(t);
    }
	delay(1000);
}