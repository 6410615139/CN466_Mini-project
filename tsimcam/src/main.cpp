#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <PubSubClient.h>
#include <cam_dev.h>
#include "root_ca.h"
#include "esp_heap_caps.h"

#define IMAGE_BUF_SIZE (1024 * 1024)  // 1 MB buffer for image
static uint8_t* image_buf = nullptr;  // Pointer to buffer in PSRAM

const char* ssid = "Khaw_cafe_2.4GHz";
const char* password = "commontu88";

const char* mqttServer = "mqtt.eclipseprojects.io";
const int mqttPort = 1883;
const char* mqttTopic = "/flask/message";
const char* mqttCarTopic = "/flask/car";  // New topic for car-related commands

const char* uploadPath = "https://6n8xrbwf-5002.asse.devtunnels.ms/image/upload_image";
const char* videoPath = "https://6n8xrbwf-5002.asse.devtunnels.ms/image/video";

WiFiClient espClient;
PubSubClient mqttClient(espClient);
WiFiClientSecure clientSecure;

// Task handles for the MQTT and continuous capture threads
TaskHandle_t mqttTaskHandle = NULL;
TaskHandle_t continuousCaptureTaskHandle = NULL;
bool isContinuousCaptureRunning = false;  // Flag to track if the continuous capture task is running

// Forward declarations
void mqttHandlerTask(void *pvParameters);
void continuousCaptureTask(void *pvParameters);
void captureAndUploadImage(const char* url);

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    String msg;
    for (unsigned int i = 0; i < length; i++) {
        msg += (char)payload[i];
    }

    // Log the raw message received
    Serial.print("Message arrived on topic: ");
    Serial.println(topic);
    Serial.print("Message: ");
    Serial.println(msg);  // Log the raw message

    // Check if the message is from the "/flask/message" topic
    if (String(topic) == mqttTopic) {
        // Check if the message is exactly "snap"
        if (msg == "snap") {
            // Capture and upload the image to the server
            captureAndUploadImage(uploadPath);
            
            // After upload, publish "done" to the topic
            mqttClient.publish(mqttTopic, "done");
        }
    }

    // Check if the message is from the "/flask/car" topic
    if (String(topic) == mqttCarTopic) {
        // Start capturing images if the message is "car"
        if (msg == "car" && !isContinuousCaptureRunning) {
            xTaskCreatePinnedToCore(continuousCaptureTask, "Continuous Capture Task", 8192, NULL, 1, &continuousCaptureTaskHandle, 1);
            isContinuousCaptureRunning = true;
        }
        // Stop capturing images if the message is "free"
        else if (msg == "free" && isContinuousCaptureRunning) {
            vTaskDelete(continuousCaptureTaskHandle);  // Delete the continuous capture task
            isContinuousCaptureRunning = false;
        }
    }
}

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);

    // Check if PSRAM is available
    if (psramFound()) {
        image_buf = (uint8_t*)heap_caps_malloc(IMAGE_BUF_SIZE, MALLOC_CAP_SPIRAM);
        if (image_buf != nullptr) {
            Serial.println("Image buffer allocated in PSRAM.");
        } else {
            Serial.println("Failed to allocate image buffer in PSRAM.");
        }
    } else {
        Serial.println("PSRAM not found.");
    }

    // WiFi connection setup
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("Connected to WiFi");

    // Initialize camera
    if (!cam_dev_init()) {
        Serial.println("Camera init failed");
        while (1);
    }
    Serial.println("Camera initialized");

    // Set up MQTT
    mqttClient.setServer(mqttServer, mqttPort);
    mqttClient.setCallback(mqttCallback);

    // Connect to MQTT broker
    while (!mqttClient.connected()) {
        Serial.print("Connecting to MQTT...");
        if (mqttClient.connect("TSIMCAM_Client")) {
            Serial.println("connected");
            mqttClient.subscribe(mqttTopic);
            mqttClient.subscribe(mqttCarTopic);  // Subscribe to the /flask/car topic
        } else {
            Serial.print("failed, rc=");
            Serial.print(mqttClient.state());
            Serial.println(" try again in 5 seconds");
            delay(5000);
        }
    }

    // Create MQTT handler task
    xTaskCreatePinnedToCore(mqttHandlerTask, "MQTT Handler Task", 8192, NULL, 1, &mqttTaskHandle, 1);
}

// Modified function to capture and upload image to a specific URL
void captureAndUploadImage(const char* url) {
    int image_size = cam_dev_snapshot(image_buf);
    if (image_size > 0) {
        HTTPClient http;
        // Temporarily disabling SSL verification for debugging
        clientSecure.setInsecure();  // This skips the SSL certificate verification
        http.begin(clientSecure, url);
        http.setTimeout(5000);  // Set timeout to avoid long waits

        String boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW";
        String form_data_start = "--" + boundary + "\r\n" +
                                 "Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n" +
                                 "Content-Type: image/jpeg\r\n\r\n";
        String form_data_end = "\r\n--" + boundary + "--\r\n";

        int total_length = form_data_start.length() + image_size + form_data_end.length();
        char *body = (char*)malloc(total_length);

        memcpy(body, form_data_start.c_str(), form_data_start.length());
        memcpy(body + form_data_start.length(), image_buf, image_size);
        memcpy(body + form_data_start.length() + image_size, form_data_end.c_str(), form_data_end.length());

        http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
        int httpResponseCode = http.POST((uint8_t*)body, total_length);

        if (httpResponseCode > 0) {
            Serial.print("Image upload successful, HTTP response code: ");
            Serial.println(httpResponseCode);
        } else {
            Serial.print("Error on image upload, code: ");
            Serial.println(httpResponseCode);
        }

        free(body);
        http.end();
    } else {
        Serial.println("Failed to capture image");
    }
}

// Task to handle MQTT loop for receiving "snap" messages
void mqttHandlerTask(void *pvParameters) {
    while (true) {
        mqttClient.loop();  // Maintain MQTT connection and handle callbacks
        delay(100);  // Small delay to avoid excessive looping
    }
}

// Task for continuously capturing and uploading an image every 1 second
void continuousCaptureTask(void *pvParameters) {
    while (true) {
        captureAndUploadImage(videoPath);  // Capture and upload to /image/video path every second
        delay(50);  // 1-second delay between uploads
    }
}

void loop() {
    // The loop function is empty because all tasks are handled in separate threads
}
