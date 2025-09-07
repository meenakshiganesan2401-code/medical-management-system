/*
 * NodeMCU 1.0 12-E Servo Control for Medical Dispensing System
 * 
 * This code controls a servo motor to dispense medicine when triggered
 * by the web application. The servo rotates to dispense medicine and
 * returns to original position.
 * 
 * Hardware Setup:
 * - Servo motor connected to D4 (GPIO2)
 * - LED indicator on D2 (GPIO4) for status
 * - Button on D3 (GPIO0) for manual testing
 * 
 * Network Setup:
 * - Connect to WiFi network
 * - Create web server on port 80
 * - Accept POST requests to /dispense endpoint
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <Servo.h>
#include <ArduinoJson.h>

// WiFi credentials - Change these to your network
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Pin definitions
const int SERVO_PIN = 2;    // D4 - Servo motor
const int LED_PIN = 4;      // D2 - Status LED
const int BUTTON_PIN = 0;   // D3 - Manual test button

// Servo settings
const int SERVO_REST_POSITION = 0;    // Rest position (0 degrees)
const int SERVO_DISPENSE_POSITION = 90; // Dispense position (90 degrees)
const int DISPENSE_DELAY = 2000;      // Time to hold dispense position (2 seconds)

// Create objects
Servo medicineServo;
ESP8266WebServer server(80);

// Variables
bool isDispensing = false;
unsigned long lastDispenseTime = 0;
int buttonState = HIGH;
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.println("\n=== Medical Dispensing System ===");
  
  // Initialize pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Initialize servo
  medicineServo.attach(SERVO_PIN);
  medicineServo.write(SERVO_REST_POSITION);
  
  // Turn on LED to indicate startup
  digitalWrite(LED_PIN, HIGH);
  
  // Connect to WiFi
  connectToWiFi();
  
  // Setup web server routes
  setupWebServer();
  
  // Start web server
  server.begin();
  Serial.println("Web server started");
  
  // Turn off LED after successful startup
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("System ready!");
  Serial.print("Server IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // Handle web server requests
  server.handleClient();
  
  // Handle manual button press
  handleButtonPress();
  
  // Handle dispensing sequence
  handleDispensing();
  
  // Small delay to prevent overwhelming the system
  delay(10);
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    // Blink LED while connecting
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
  
  Serial.println("");
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

// Function to extract JSON values (simple parser)
String extractJsonValue(String json, String key) {
  String searchKey = "\"" + key + "\":";
  int startIndex = json.indexOf(searchKey);
  if (startIndex == -1) return "";
  
  startIndex += searchKey.length();
  
  // Skip whitespace
  while (startIndex < json.length() && (json.charAt(startIndex) == ' ' || json.charAt(startIndex) == '\t')) {
    startIndex++;
  }
  
  // Check if value is quoted
  bool isQuoted = (startIndex < json.length() && json.charAt(startIndex) == '"');
  if (isQuoted) startIndex++;
  
  int endIndex = startIndex;
  if (isQuoted) {
    // Find closing quote
    while (endIndex < json.length() && json.charAt(endIndex) != '"') {
      endIndex++;
    }
  } else {
    // Find comma or closing brace
    while (endIndex < json.length() && json.charAt(endIndex) != ',' && json.charAt(endIndex) != '}') {
      endIndex++;
    }
  }
  
  return json.substring(startIndex, endIndex);
}

void setupWebServer() {
  // Root endpoint - system status
  server.on("/", HTTP_GET, []() {
    String html = "<!DOCTYPE html><html><head><title>Medical Dispensing System</title>";
    html += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>";
    html += "<style>body{font-family:Arial,sans-serif;text-align:center;padding:20px;}";
    html += ".status{background:#f0f0f0;padding:20px;border-radius:10px;margin:20px;}";
    html += ".success{background:#d4edda;color:#155724;}";
    html += ".error{background:#f8d7da;color:#721c24;}</style></head><body>";
    html += "<h1>Medical Dispensing System</h1>";
    html += "<div class='status success'>";
    html += "<h2>System Online</h2>";
    html += "<p>NodeMCU is connected and ready</p>";
    html += "<p>IP: " + WiFi.localIP().toString() + "</p>";
    html += "<p>Uptime: " + String(millis() / 1000) + " seconds</p>";
    html += "</div>";
    html += "<div class='status'>";
    html += "<h3>Endpoints</h3>";
    html += "<p><strong>GET /</strong> - System status</p>";
    html += "<p><strong>POST /dispense</strong> - Dispense medicine</p>";
    html += "<p><strong>GET /status</strong> - JSON status</p>";
    html += "</div></body></html>";
    
    server.send(200, "text/html", html);
  });
  
  // Status endpoint - JSON response
  server.on("/status", HTTP_GET, []() {
    StaticJsonDocument<200> doc;
    doc["status"] = "online";
    doc["ip"] = WiFi.localIP().toString();
    doc["uptime"] = millis() / 1000;
    doc["dispensing"] = isDispensing;
    doc["servo_position"] = medicineServo.read();
    
    String response;
    serializeJson(doc, response);
    server.send(200, "application/json", response);
  });
  
  // Dispense endpoint - main functionality
  server.on("/dispense", HTTP_POST, []() {
    Serial.println("Dispense request received");
    
    if (isDispensing) {
      server.send(409, "application/json", "{\"error\":\"Already dispensing\"}");
      return;
    }
    
    // Parse JSON data from request
    if (server.hasArg("plain")) {
      String body = server.arg("plain");
      Serial.println("Received data: " + body);
      
      // Parse JSON (basic parsing for key fields)
      String patientName = extractJsonValue(body, "patient_name");
      String medicineName = extractJsonValue(body, "medicine_name");
      String dosage = extractJsonValue(body, "dosage");
      String frequency = extractJsonValue(body, "frequency");
      String quantity = extractJsonValue(body, "quantity");
      String notes = extractJsonValue(body, "notes");
      String dispensedBy = extractJsonValue(body, "dispensed_by");
      String timestamp = extractJsonValue(body, "timestamp");
      
      // Print prescription details
      Serial.println("=== PRESCRIPTION DISPENSING ===");
      Serial.println("Patient: " + patientName);
      Serial.println("Medicine: " + medicineName);
      Serial.println("Dosage: " + dosage);
      Serial.println("Frequency: " + frequency);
      Serial.println("Quantity: " + quantity);
      Serial.println("Notes: " + notes);
      Serial.println("Dispensed by: " + dispensedBy);
      Serial.println("Time: " + timestamp);
      Serial.println("================================");
      
      // Calculate dispensing time based on quantity
      int quantityInt = quantity.toInt();
      if (quantityInt <= 0) quantityInt = 1;
      if (quantityInt > 10) quantityInt = 10; // Safety limit
      
      // Start dispensing sequence
      isDispensing = true;
      lastDispenseTime = millis();
      
      // Turn on LED to indicate dispensing
      digitalWrite(LED_PIN, HIGH);
      
      // Dispense based on quantity
      for (int i = 0; i < quantityInt; i++) {
        Serial.println("Dispensing tablet " + String(i + 1) + " of " + String(quantityInt));
        
        // Move servo to dispense position
        medicineServo.write(SERVO_DISPENSE_POSITION);
        delay(1000); // Hold position for 1 second
        
        // Return to rest position
        medicineServo.write(SERVO_REST_POSITION);
        delay(500); // Wait between tablets
        
        // Blink LED for each tablet
        digitalWrite(LED_PIN, LOW);
        delay(200);
        digitalWrite(LED_PIN, HIGH);
      }
      
      Serial.println("All tablets dispensed successfully");
      
      // Send success response with prescription details
      String response = "{\"status\":\"dispensed\",\"message\":\"Medicine dispensed successfully\",";
      response += "\"patient\":\"" + patientName + "\",";
      response += "\"medicine\":\"" + medicineName + "\",";
      response += "\"quantity\":" + quantity + "}";
      server.send(200, "application/json", response);
    } else {
      // Fallback for simple requests without JSON
      isDispensing = true;
      lastDispenseTime = millis();
      digitalWrite(LED_PIN, HIGH);
      medicineServo.write(SERVO_DISPENSE_POSITION);
      Serial.println("Servo moved to dispense position (simple mode)");
      server.send(200, "application/json", "{\"status\":\"dispensing\",\"message\":\"Medicine dispensed successfully\"}");
    }
  });
  
  // Prescriptions endpoint - receive all patient prescriptions
  server.on("/prescriptions", HTTP_POST, []() {
    Serial.println("Prescriptions data received");
    
    if (server.hasArg("plain")) {
      String body = server.arg("plain");
      Serial.println("Received prescriptions data: " + body);
      
      // Parse JSON data
      String patientName = extractJsonValue(body, "patient_name");
      String patientId = extractJsonValue(body, "patient_id");
      String totalPrescriptions = extractJsonValue(body, "total_prescriptions");
      String sentBy = extractJsonValue(body, "sent_by");
      String timestamp = extractJsonValue(body, "timestamp");
      
      // Print prescription summary
      Serial.println("=== PRESCRIPTIONS RECEIVED ===");
      Serial.println("Patient: " + patientName);
      Serial.println("Patient ID: " + patientId);
      Serial.println("Total Prescriptions: " + totalPrescriptions);
      Serial.println("Sent by: " + sentBy);
      Serial.println("Time: " + timestamp);
      Serial.println("==============================");
      
      // Parse individual prescriptions (simplified parsing)
      int prescriptionCount = totalPrescriptions.toInt();
      for (int i = 0; i < prescriptionCount && i < 10; i++) { // Limit to 10 prescriptions
        String medicineName = extractJsonValue(body, "medicine_name");
        String dosage = extractJsonValue(body, "dosage");
        String frequency = extractJsonValue(body, "frequency");
        
        if (medicineName.length() > 0) {
          Serial.println("Prescription " + String(i + 1) + ":");
          Serial.println("  Medicine: " + medicineName);
          Serial.println("  Dosage: " + dosage);
          Serial.println("  Frequency: " + frequency);
        }
      }
      
      // Blink LED to indicate data received
      for (int i = 0; i < 3; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(200);
        digitalWrite(LED_PIN, LOW);
        delay(200);
      }
      
      // Send success response
      String response = "{\"status\":\"received\",\"message\":\"Prescriptions received successfully\",";
      response += "\"patient\":\"" + patientName + "\",";
      response += "\"count\":" + totalPrescriptions + "}";
      server.send(200, "application/json", response);
    } else {
      server.send(400, "application/json", "{\"error\":\"No data received\"}");
    }
  });
  
  // Handle 404 errors
  server.onNotFound([]() {
    server.send(404, "application/json", "{\"error\":\"Endpoint not found\"}");
  });
}

void handleButtonPress() {
  // Read button state
  int reading = digitalRead(BUTTON_PIN);
  
  // Check for button state change (debouncing)
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }
  
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != buttonState) {
      buttonState = reading;
      
      // Button pressed (LOW because of INPUT_PULLUP)
      if (buttonState == LOW) {
        Serial.println("Manual dispense button pressed");
        
        if (!isDispensing) {
          isDispensing = true;
          lastDispenseTime = millis();
          digitalWrite(LED_PIN, HIGH);
          medicineServo.write(SERVO_DISPENSE_POSITION);
          Serial.println("Manual dispense initiated");
        }
      }
    }
  }
  
  lastButtonState = reading;
}

void handleDispensing() {
  if (isDispensing && (millis() - lastDispenseTime) >= DISPENSE_DELAY) {
    // Dispensing sequence complete
    medicineServo.write(SERVO_REST_POSITION);
    digitalWrite(LED_PIN, LOW);
    isDispensing = false;
    
    Serial.println("Dispensing sequence completed - servo returned to rest position");
  }
}

// Additional utility functions
void blinkLED(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs);
  }
}

void resetSystem() {
  Serial.println("Resetting system...");
  medicineServo.write(SERVO_REST_POSITION);
  digitalWrite(LED_PIN, LOW);
  isDispensing = false;
  delay(1000);
  ESP.restart();
}
