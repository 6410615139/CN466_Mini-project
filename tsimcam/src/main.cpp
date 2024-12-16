#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <PubSubClient.h>
#include <cam_dev.h>
#include "root_ca.h"
#include "esp_heap_caps.h"

#define IMAGE_BUF_SIZE (1024 * 1024)
static uint8_t* image_buf = nullptr;

const char* ssid = "Khaw_cafe_2.4GHz";
const char* password = "commontu88";

const char* bound = "/in";
const char* gate = "bound/gate1";
const char* server = "https://6n8xrbwf-5002.asse.devtunnels.ms";
const char* mqttServer = "mqtt.eclipseprojects.io";
const int mqttPort = 1883;

char mqttCameraTopic[50];
char videoPath[100];

WiFiClient espClient;
PubSubClient mqttClient(espClient);
WiFiClientSecure clientSecure;
TaskHandle_t mqttTaskHandle = NULL;
TaskHandle_t continuousCaptureTaskHandle = NULL;
bool isContinuousCaptureRunning = false;

void mqttHandlerTask(void *pvParameters);
void continuousCaptureTask(void *pvParameters);
void captureAndUploadImage(const char* url);

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    String msg;
    for (unsigned int i = 0; i < length; i++) {
        msg += (char)payload[i];
    }
    Serial.print("Message arrived on topic: ");
    Serial.println(topic);
    Serial.print("Message: ");
    Serial.println(msg);
    
    if (String(topic) == mqttCameraTopic) {
        if (msg == "enable" && !isContinuousCaptureRunning) {
            xTaskCreatePinnedToCore(continuousCaptureTask, "Continuous Capture Task", 8192, NULL, 1, &continuousCaptureTaskHandle, 1);
            isContinuousCaptureRunning = true;
        } else if (msg == "disable" && isContinuousCaptureRunning) {
            isContinuousCaptureRunning = false;  // Stop the task safely
        }
    }
}

void setup() {
    strcpy(mqttCameraTopic, bound);
    strcat(mqttCameraTopic, gate);

    strcpy(videoPath, server);
    strcat(videoPath, bound);
    strcat(videoPath, "image/video");

    Serial.begin(115200);
    WiFi.begin(ssid, password);

    if (psramFound()) {
        image_buf = (uint8_t*)heap_caps_malloc(IMAGE_BUF_SIZE, MALLOC_CAP_SPIRAM);
    } else {
        image_buf = (uint8_t*)malloc(IMAGE_BUF_SIZE);  // Fallback to heap memory
    }

    if (image_buf == nullptr) {
        Serial.println("Failed to allocate image buffer.");
    } else {
        Serial.println("Image buffer allocated.");
    }

    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("Connected to WiFi");

    if (!cam_dev_init()) {
        Serial.println("Camera init failed");
        while (1);
    }
    delay(1000);
    Serial.println("Camera initialized");

    mqttClient.setServer(mqttServer, mqttPort);
    mqttClient.setCallback(mqttCallback);

    while (!mqttClient.connected()) {
        Serial.print("Connecting to MQTT...");
        if (mqttClient.connect("TSIMCAM_Client")) {
            Serial.println("connected");
            mqttClient.subscribe(mqttCameraTopic);
        } else {
            Serial.print("failed, rc=");
            Serial.print(mqttClient.state());
            Serial.println(" try again in 5 seconds");
            delay(5000);
        }
    }

    xTaskCreatePinnedToCore(mqttHandlerTask, "MQTT Handler Task", 8192, NULL, 1, &mqttTaskHandle, 1);
}

void captureAndUploadImage(const char* url) {
    if (image_buf == nullptr) {
        Serial.println("Image buffer is not allocated. Skipping capture.");
        return;
    }

    int image_size = cam_dev_snapshot(image_buf);
    if (image_size <= 0) {
        Serial.println("Failed to capture image or invalid image size.");
        return;
    }

    HTTPClient http;
    clientSecure.setCACert(certificate);
    http.begin(clientSecure, url);
    http.setTimeout(5000);

    String boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW";
    String form_data_start = "--" + boundary + "\r\n" +
                             "Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n" +
                             "Content-Type: image/jpeg\r\n\r\n";
    String form_data_end = "\r\n--" + boundary + "--\r\n";

    int total_length = form_data_start.length() + image_size + form_data_end.length();
    char *body = (char*)malloc(total_length);
    if (body == nullptr) {
        Serial.println("Failed to allocate memory for HTTP body.");
        return;
    }

    memcpy(body, form_data_start.c_str(), form_data_start.length());
    memcpy(body + form_data_start.length(), image_buf, image_size);
    memcpy(body + form_data_start.length() + image_size, form_data_end.c_str(), form_data_end.length());

    http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
    int httpResponseCode = http.POST((uint8_t*)body, total_length);

    if (httpResponseCode > 0) {
        Serial.print("Image upload successful, HTTP response code: ");
        Serial.println(httpResponseCode);
        String response = http.getString();
        Serial.print("Response message: ");
        Serial.println(response);
    } else {
        Serial.print("Error on image upload, code: ");
        Serial.println(httpResponseCode);
    }

    free(body);
    http.end();
}

void mqttHandlerTask(void *pvParameters) {
    while (true) {
        mqttClient.loop();
        delay(100);
    }
}

void continuousCaptureTask(void *pvParameters) {
    while (isContinuousCaptureRunning) {
        captureAndUploadImage(videoPath);
        delay(1000);
    }
    vTaskDelete(NULL);  // Delete the task itself when loop ends
}

void loop() {
    delay(100);
}
