// Define the pin connections
const int thermoDO = 4; // Data Output from MAX6675
const int thermoCS = 5; // Chip Select
const int thermoCLK = 6; // Clock

void setup() {
  pinMode(thermoCS, OUTPUT);
  pinMode(thermoCLK, OUTPUT);
  pinMode(thermoDO, INPUT);

  digitalWrite(thermoCS, HIGH);
  digitalWrite(thermoCLK, LOW);
  Serial.begin(9600);
}

uint16_t readMAX6675() {
  uint16_t v = 0;
  digitalWrite(thermoCS, HIGH);
  delay(1);
  digitalWrite(thermoCS, LOW);
  delay(1);

  // Read 16 bits from MAX6675
  for (int i = 15; i >= 0; i--) {
    digitalWrite(thermoCLK, HIGH);
    delay(1);
    // Serial.print(digitalRead(thermoDO));
    if (digitalRead(thermoDO)) {
      v |= 1 << i;
    }
    digitalWrite(thermoCLK, LOW);
    delay(1);
  }

  digitalWrite(thermoCS, HIGH);
  
  // Check if thermocouple is open
  // if (v & 0x4) {
  //   // Handle error: No thermocouple connected
  //   return NAN;
  // }

  // Convert to temperature in Celsius
  v >>= 3;
  return v;
}

void loop() {
  if (Serial.available() > 0) {
    // Read the incoming byte:
    String incomingData = Serial.readStringUntil('#');
    
    // Check if the received command is "*S#"
    if (incomingData == "*S") {
      uint16_t temperature = readMAX6675();
      
      // Check if temperature reading was successful
      if (!isnan(temperature)) {
        // Send the temperature data in the format "*<value>#"
        Serial.print("*");
        Serial.print(temperature);
        Serial.print("#\n");
      } else {
        // Send an error message if temperature reading failed
        Serial.print("*Error#\n");
      }
    }
  }
}
