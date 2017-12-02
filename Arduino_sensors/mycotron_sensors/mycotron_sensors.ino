/**************** Sensors Module V1.3 for Mushroom Project ***********************
Author:  ekulyyev: kea2288@yandex.ru
         username: email@address
         
Lisence: N/A

Note:    This piece of source code is supposed to be used as a demostration ONLY. More
         sophisticated calibration is required for industrial field application. 
         
                                                           Mycotronics    2017-10-31
************************************************************************************/

#include <math.h>
#include "DHT.h"
#include "FastLED.h"

#define NUM_LEDS 60
#define DHTPIN  2     // Temperature and humidity pin
#define RELE_1  3     // Relay pin humidifier
#define RELE_2  4     // Relay pin peltier
#define RELE_3  5     // Relay pin vent
#define DATA_PIN 6    // NeoPixel pin
#define DHTTYPE DHT22   // DHT 22  (AM2302)
#define CO2PIN  A0      // CO2 sensor pin

DHT dht(DHTPIN, DHTTYPE);
int val = 0;
float h;
float t;
String incomingByte;
/* ****** Commands from RPi ******* */
String on_rel1_cmd   = "relay1:on\n";
String off_rel1_cmd  = "relay1:off\n";
String on_rel2_cmd   = "relay2:on\n";
String off_rel2_cmd  = "relay2:off\n";
String on_rel3_cmd   = "relay3:on\n";
String off_rel3_cmd  = "relay3:off\n";
String on_light_cmd  = "light:on\n";
String off_light_cmd = "light:off\n";
/* ******************************** */
CRGB leds[NUM_LEDS];
int i; // NeoPixel led counter

void setup() 
{
    // Initialize serial
    Serial.begin(9600);
    dht.begin();
    pinMode(RELE_1, OUTPUT);
    pinMode(RELE_2, OUTPUT);
    pinMode(RELE_3, OUTPUT);
    FastLED.addLeds<NEOPIXEL, DATA_PIN>(leds, NUM_LEDS);
    FastLED.show();
}

void loop() 
{
    // Read values from CO2 sensor
    val = analogRead(CO2PIN);
    Serial.print("CO2: ");
    Serial.println(val);

    // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
    h = dht.readHumidity();
    t = dht.readTemperature();

    // Check if returns are valid, if they are NaN (not a number) then something went wrong!
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

    Serial.flush();

    if(Serial.available() > 0)
    {

        // Read the incomign bytes
        incomingByte = Serial.readString();

        // Rrint what we got
        Serial.print("I recieved: ");
        Serial.println(incomingByte);

        // Check command of light and turn on/off
        if(incomingByte == on_light_cmd)
        {
            Serial.println("Light is ON!");

            // Turn on all led
            for (i=0; i<NUM_LEDS; i++)
            {
                leds[i] = CRGB::Blue; 
            }
            FastLED.show();
        }
        else if(incomingByte == on_light_cmd)
        {
            Serial.println("Light is OFF!");

            // Turn off all led
            for (i=0; i<NUM_LEDS; i++)
            {
                leds[i] = CRGB::Black; 
            }
            FastLED.show();
        }

        // Check command of relays and turn on/off
        check_cmd(RELE_1, incomingByte, on_rel1_cmd, off_rel1_cmd, "RELE1");
        check_cmd(RELE_2, incomingByte, on_rel2_cmd, off_rel2_cmd, "RELE2");
        check_cmd(RELE_3, incomingByte, on_rel3_cmd, off_rel3_cmd, "RELE3");


        
    }

    Serial.flush();
    incomingByte = "\0";
    delay(100);  
}

void check_cmd(int pin, String rpicmd, String on_cmd, String off_cmd, String s)
{
    // Check command of relay2 and turn on/off
    if(rpicmd == on_cmd)
    {
        Serial.println(s);
        Serial.println(" is ON!");
        digitalWrite(pin, HIGH);
    }
    else if(rpicmd == off_cmd)
    {
        Serial.println(s);
        Serial.println(" is OFF!");
        digitalWrite(pin, LOW);
    }
}
