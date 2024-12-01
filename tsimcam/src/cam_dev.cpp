#include <Arduino.h>
#include <esp_camera.h>

// static variables
camera_config_t camera_config = {
    .pin_pwdn = -1,
    .pin_reset = 18,
    .pin_xclk = 14,
    .pin_sscb_sda = 4,
    .pin_sscb_scl = 5,
    .pin_d7 = 15,
    .pin_d6 = 16,
    .pin_d5 = 17,
    .pin_d4 = 12,
    .pin_d3 = 10,
    .pin_d2 = 8,
    .pin_d1 = 9,
    .pin_d0 = 11,
    .pin_vsync = 6,
    .pin_href = 7,
    .pin_pclk = 13,
    .xclk_freq_hz = 20000000,
    .ledc_timer = LEDC_TIMER_0,
    .ledc_channel = LEDC_CHANNEL_0,
    .pixel_format = PIXFORMAT_JPEG,  // JPEG compression
    .frame_size = FRAMESIZE_UXGA,   // 1600x1200 resolution
    .jpeg_quality = 10,              // Compression quality (lower = better quality)
    .fb_count = 1                    // Number of frame buffers
};

bool cam_dev_init(void) {
    esp_err_t err = esp_camera_init(&camera_config);
    if (err != ESP_OK) {
        Serial.print("Camera Init Failed");
        return false;
    }
    Serial.print("Camera Init Success");

    // Optional: Adjust sensor settings for consistent output
    sensor_t *s = esp_camera_sensor_get();
    if (s != NULL) {
        // Enable auto white balance for realistic color temperature
        s->set_whitebal(s, 1);        // Enable auto white balance
        
        // Adjust exposure settings for better image in varied lighting
        s->set_exposure_ctrl(s, 1);   // Enable auto exposure
        s->set_gain_ctrl(s, 1);       // Enable auto gain for better low-light performance
        
        // Adjust other parameters as needed
        s->set_brightness(s, 0);      // Default brightness
        s->set_contrast(s, 0);        // Default contrast
        s->set_saturation(s, 0);      // Default saturation (0 = normal)
    }

    return true;
}

int cam_dev_snapshot(uint8_t *out_buf) {
    int buf_sz = 0;
    camera_fb_t *pic = esp_camera_fb_get();  // Capture a frame
    buf_sz = pic->len;
    memcpy(out_buf, pic->buf, buf_sz);  // Copy image data to output buffer
    esp_camera_fb_return(pic);  // Return the frame buffer to the pool

    return buf_sz;
}
