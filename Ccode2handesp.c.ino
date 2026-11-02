#include <ESP32Servo.h>
#include <stdlib.h>
#include <string.h>

#define THUMB_PIN   13
#define INDEX_PIN   12
#define MIDDLE_PIN  14
#define RING_PIN    27
#define PINKY_PIN   26
#define WRIST_PIN   25

#define NUM_SERVOS 6

Servo thumbServo;
Servo indexServo;
Servo middleServo;
Servo ringServo;
Servo pinkyServo;
Servo wristServo;

Servo* servos[NUM_SERVOS] = {
  &thumbServo,
  &indexServo,
  &middleServo,
  &ringServo,
  &pinkyServo,
  &wristServo
};


const int SERVO_STEP = 10;
const int SERVO_UPDATE_DELAY = 1;

const int SERVO_MIN = 0;
const int SERVO_MAX = 180;

const int SERVO_MIN_PULSE = 500;
const int SERVO_MAX_PULSE = 2500;

const int SERVO_FREQUENCY = 50;

// SERVO ANGLES

int target[NUM_SERVOS] = {
  10, 10, 10, 10, 10, 90
};

int current[NUM_SERVOS] = {
  10, 10, 10, 10, 10, 90
};


#define BAUD_RATE 115200

char inputBuffer[80];

int inputLen = 0;
const int MAX_INPUT_LENGTH = 80;

const bool SERIAL_FAILSAFE = false;

const unsigned long SERIAL_TIMEOUT = 1000;

unsigned long lastSerialTime = 0;


void setup()
{
  Serial.begin(BAUD_RATE);

  delay(500);

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  thumbServo.setPeriodHertz(SERVO_FREQUENCY);
  indexServo.setPeriodHertz(SERVO_FREQUENCY);
  middleServo.setPeriodHertz(SERVO_FREQUENCY);
  ringServo.setPeriodHertz(SERVO_FREQUENCY);
  pinkyServo.setPeriodHertz(SERVO_FREQUENCY);
  wristServo.setPeriodHertz(SERVO_FREQUENCY);

  thumbServo.attach(THUMB_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  indexServo.attach(INDEX_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  middleServo.attach(MIDDLE_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  ringServo.attach(RING_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  pinkyServo.attach(PINKY_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  wristServo.attach(WRIST_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    current[i] = target[i];

    servos[i]->write(current[i]);
  }

  lastSerialTime = millis();

  Serial.println();
  Serial.println("======================================");
  Serial.println("ESP32 ROBOTIC HAND READY");
  Serial.println("6 SERVO CAMERA + VOICE CONTROLLER");
  Serial.println("======================================");

  Serial.println("Waiting for Python commands...");
}

void readSerial()
{
  while (Serial.available() > 0)
  {
    char c = Serial.read();

    if (c == '\n' || c == '\r')
    {
      if (inputLen > 0)
      {
        inputBuffer[inputLen] = '\0';

        processData(inputBuffer);

        inputLen = 0;
      }
    }
    else
    {
      if (inputLen < MAX_INPUT_LENGTH - 1)
      {
        inputBuffer[inputLen++] = c;
      }
      else
      {
        inputLen = 0;
      }
    }
  }
}


void processData(char* data)
{
  int values[NUM_SERVOS];

  int count = 0;

  char* token = strtok(data, ",");

  while (token != NULL && count < NUM_SERVOS)
  {
    char* end;

    long value = strtol(token, &end, 10);

    if (end == token || *end != '\0')
    {
      return;
    }

    values[count] = constrain(
      (int)value,
      SERVO_MIN,
      SERVO_MAX
    );

    count++;

    token = strtok(NULL, ",");
  }

  if (count == NUM_SERVOS && token == NULL)
  {
    for (int i = 0; i < NUM_SERVOS; i++)
    {
      target[i] = values[i];
    }

    lastSerialTime = millis();
  }
}


void updateServos()
{
  for (int i = 0; i < NUM_SERVOS; i++)
  {
    if (current[i] < target[i])
    {
      current[i] += SERVO_STEP;

      if (current[i] > target[i])
      {
        current[i] = target[i];
      }
    }

    else if (current[i] > target[i])
    {
      current[i] -= SERVO_STEP;

      if (current[i] < target[i])
      {
        current[i] = target[i];
      }
    }

    current[i] = constrain(
      current[i],
      SERVO_MIN,
      SERVO_MAX
    );

    servos[i]->write(current[i]);
  }
}



void serialFailsafe()
{
  if (!SERIAL_FAILSAFE)
  {
    return;
  }

  if (millis() - lastSerialTime > SERIAL_TIMEOUT)
  {
    target[0] = 180;
    target[1] = 0;
    target[2] = 180;
    target[3] = 0;
    target[4] = 180;
    target[5] = 90;
  }
}


void loop()
{
  readSerial();

  serialFailsafe();

  updateServos();

  delay(SERVO_UPDATE_DELAY);
}

