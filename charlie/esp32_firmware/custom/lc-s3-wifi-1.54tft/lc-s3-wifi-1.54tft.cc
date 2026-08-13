#include "wifi_board.h"
#include "codecs/es8311_audio_codec.h"
#include "display/lcd_display.h"
#include "application.h"
#include "button.h"
#include "config.h"
#include "led/single_led.h"
#include "boards/common/power_save_timer.h"
#include "assets/lang_config.h"

#include <esp_log.h>
#include <esp_err.h>
#include <esp_lcd_panel_vendor.h>
#include <esp_lcd_panel_io.h>
#include <esp_lcd_panel_ops.h>
#include <driver/i2c_master.h>
#include <driver/spi_common.h>
#include <driver/gpio.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#define TAG "lc_s3_wifi_1_54tft"

class LcS3Board : public WifiBoard {
private:
    Button boot_button_;
    Button volume_up_button_;
    Button volume_down_button_;
    SingleLed* led_;
    LcdDisplay* display_;
    i2c_master_bus_handle_t codec_i2c_bus_;
    PowerSaveTimer* power_save_timer_;
    esp_lcd_panel_io_handle_t panel_io_ = nullptr;
    esp_lcd_panel_handle_t panel_ = nullptr;

    void InitializePowerSaveTimer() {
        power_save_timer_ = new PowerSaveTimer(240, 240, -1);
        power_save_timer_->OnEnterSleepMode([this]() {
            ESP_LOGI(TAG, "Entering power save mode");
            GetDisplay()->SetPowerSaveMode(true);
        });
        power_save_timer_->OnExitSleepMode([this]() {
            ESP_LOGI(TAG, "Exiting power save mode");
            GetDisplay()->SetPowerSaveMode(false);
        });
        power_save_timer_->SetEnabled(true);
    }

    void InitializeLed() {
        led_ = new SingleLed(BUILTIN_LED_GPIO);
    }

    void InitializeSpi() {
        spi_bus_config_t buscfg = {};
        buscfg.mosi_io_num = DISPLAY_SDA;
        buscfg.miso_io_num = GPIO_NUM_NC;
        buscfg.sclk_io_num = DISPLAY_SCL;
        buscfg.quadwp_io_num = GPIO_NUM_NC;
        buscfg.quadhd_io_num = GPIO_NUM_NC;
        buscfg.max_transfer_sz = DISPLAY_WIDTH * DISPLAY_HEIGHT * sizeof(uint16_t);
        ESP_ERROR_CHECK(spi_bus_initialize(SPI3_HOST, &buscfg, SPI_DMA_CH_AUTO));
    }

    void InitializeSt7789Display() {
        // Manual hardware reset
        gpio_config_t config = {};
        config.pin_bit_mask = (1ULL << DISPLAY_RES);
        config.mode = GPIO_MODE_OUTPUT;
        ESP_ERROR_CHECK(gpio_config(&config));
        gpio_set_level(DISPLAY_RES, 0);
        vTaskDelay(pdMS_TO_TICKS(20));
        gpio_set_level(DISPLAY_RES, 1);
        vTaskDelay(pdMS_TO_TICKS(20));

        ESP_LOGI(TAG, "Install panel IO");
        esp_lcd_panel_io_spi_config_t io_config = {};
        io_config.cs_gpio_num = DISPLAY_CS;
        io_config.dc_gpio_num = DISPLAY_DC;
        io_config.spi_mode = 3;
        io_config.pclk_hz = 40 * 1000 * 1000;
        io_config.trans_queue_depth = 10;
        io_config.lcd_cmd_bits = 8;
        io_config.lcd_param_bits = 8;
        ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi(SPI3_HOST, &io_config, &panel_io_));

        ESP_LOGI(TAG, "Install LCD driver");
        esp_lcd_panel_dev_config_t panel_config = {};
        panel_config.reset_gpio_num = DISPLAY_RES;
        panel_config.rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB;
        panel_config.bits_per_pixel = 16;
        ESP_ERROR_CHECK(esp_lcd_new_panel_st7789(panel_io_, &panel_config, &panel_));
        ESP_ERROR_CHECK(esp_lcd_panel_reset(panel_));
        ESP_ERROR_CHECK(esp_lcd_panel_init(panel_));
        ESP_ERROR_CHECK(esp_lcd_panel_swap_xy(panel_, DISPLAY_SWAP_XY));
        ESP_ERROR_CHECK(esp_lcd_panel_mirror(panel_, DISPLAY_MIRROR_X, DISPLAY_MIRROR_Y));
        ESP_ERROR_CHECK(esp_lcd_panel_invert_color(panel_, true));

        // Exit sleep explicitly
        esp_lcd_panel_io_tx_param(panel_io_, 0x11, nullptr, 0);
        vTaskDelay(pdMS_TO_TICKS(120));

        display_ = new SpiLcdDisplay(panel_io_, panel_,
            DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_OFFSET_X, DISPLAY_OFFSET_Y,
            DISPLAY_MIRROR_X, DISPLAY_MIRROR_Y, DISPLAY_SWAP_XY);

        // Turn display on
        esp_lcd_panel_io_tx_param(panel_io_, 0x29, nullptr, 0);

        // Backlight: direct GPIO push-pull (active-high). Avoid LEDC channel/timer
        // conflicts with SingleLed on GPIO1 which also claims LEDC_CHANNEL_0.
        gpio_config_t bl_cfg = {};
        bl_cfg.pin_bit_mask = (1ULL << DISPLAY_BACKLIGHT_PIN);
        bl_cfg.mode = GPIO_MODE_OUTPUT;
        bl_cfg.pull_up_en = GPIO_PULLUP_DISABLE;
        bl_cfg.pull_down_en = GPIO_PULLDOWN_DISABLE;
        bl_cfg.intr_type = GPIO_INTR_DISABLE;
        ESP_ERROR_CHECK(gpio_config(&bl_cfg));
        gpio_set_level(DISPLAY_BACKLIGHT_PIN, 1);
        ESP_LOGI(TAG, "Backlight GPIO%d set HIGH", DISPLAY_BACKLIGHT_PIN);
    }

    void InitializeCodecI2c() {
        i2c_master_bus_config_t i2c_cfg = {};
        i2c_cfg.i2c_port = I2C_NUM_0;
        i2c_cfg.sda_io_num = AUDIO_CODEC_I2C_SDA_PIN;
        i2c_cfg.scl_io_num = AUDIO_CODEC_I2C_SCL_PIN;
        i2c_cfg.clk_source = I2C_CLK_SRC_DEFAULT;
        i2c_cfg.flags.enable_internal_pullup = true;
        ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_cfg, &codec_i2c_bus_));
    }

    void InitializeButtons() {
        boot_button_.OnClick([this]() {
            power_save_timer_->WakeUp();
            auto& app = Application::GetInstance();
            if (app.GetDeviceState() == kDeviceStateStarting) {
                EnterWifiConfigMode();
                return;
            }
            app.ToggleChatState();
        });

        volume_up_button_.OnClick([this]() {
            power_save_timer_->WakeUp();
            auto codec = GetAudioCodec();
            auto volume = codec->output_volume() + 10;
            if (volume > 100) volume = 100;
            codec->SetOutputVolume(volume);
            GetDisplay()->ShowNotification(Lang::Strings::VOLUME + std::to_string(volume));
        });
        volume_up_button_.OnLongPress([this]() {
            power_save_timer_->WakeUp();
            GetAudioCodec()->SetOutputVolume(100);
            GetDisplay()->ShowNotification(Lang::Strings::MAX_VOLUME);
        });

        volume_down_button_.OnClick([this]() {
            power_save_timer_->WakeUp();
            auto codec = GetAudioCodec();
            auto volume = codec->output_volume() - 10;
            if (volume < 0) volume = 0;
            codec->SetOutputVolume(volume);
            GetDisplay()->ShowNotification(Lang::Strings::VOLUME + std::to_string(volume));
        });
        volume_down_button_.OnLongPress([this]() {
            power_save_timer_->WakeUp();
            GetAudioCodec()->SetOutputVolume(0);
            GetDisplay()->ShowNotification(Lang::Strings::MUTED);
        });
    }

public:
    LcS3Board()
        : boot_button_(BOOT_BUTTON_GPIO),
          volume_up_button_(VOLUME_UP_BUTTON_GPIO),
          volume_down_button_(VOLUME_DOWN_BUTTON_GPIO) {
        ESP_LOGI(TAG, "LC-S3 WiFi 1.54TFT board init");
        InitializeLed();
        InitializePowerSaveTimer();
        InitializeCodecI2c();
        InitializeSpi();
        InitializeSt7789Display();
        InitializeButtons();
        GetBacklight()->SetBrightness(80);
        ESP_LOGI(TAG, "Init complete");
    }

    virtual Led* GetLed() override { return led_; }

    virtual AudioCodec* GetAudioCodec() override {
        static Es8311AudioCodec audio_codec(codec_i2c_bus_, I2C_NUM_0,
            AUDIO_INPUT_SAMPLE_RATE, AUDIO_OUTPUT_SAMPLE_RATE,
            AUDIO_I2S_GPIO_MCLK, AUDIO_I2S_GPIO_BCLK, AUDIO_I2S_GPIO_WS,
            AUDIO_I2S_GPIO_DOUT, AUDIO_I2S_GPIO_DIN,
            AUDIO_CODEC_PA_PIN, AUDIO_CODEC_ES8311_ADDR);
        return &audio_codec;
    }

    virtual Display* GetDisplay() override { return display_; }

    // Simple GPIO-based backlight (active-high). We do NOT use PwmBacklight because
    // it claims LEDC_CHANNEL_0/TIMER_0 which collides with SingleLed on GPIO1.
    virtual Backlight* GetBacklight() override {
        class GpioBacklight : public Backlight {
        protected:
            void SetBrightnessImpl(uint8_t brightness) override {
                gpio_set_level(DISPLAY_BACKLIGHT_PIN, brightness > 0 ? 1 : 0);
            }
        };
        static GpioBacklight backlight;
        return &backlight;
    }
};

DECLARE_BOARD(LcS3Board);
