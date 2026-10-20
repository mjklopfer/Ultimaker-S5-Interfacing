#pragma once
// Board-specific GPIO assignments are intentionally absent until reviewed.
// Supply these macros through build flags or the role sketch before including
// Stm32BenchApp.h. They are STM32duino uint32_t pin names, not legacy digital pin numbers.
#ifndef UMB_BOARD_CONFIGURED
#define UMB_BOARD_CONFIGURED 0
#endif
#ifndef UMB_ENABLE_TRANSPORT
#define UMB_ENABLE_TRANSPORT 0
#endif
#ifndef UMB_ENABLE_SENSORS
#define UMB_ENABLE_SENSORS 0
#endif

#if !defined(ARDUINO_ARCH_STM32) && !defined(UMB_SYNTAX_CHECK)
#error "These role sketches target STM32duino, STM32 hardware is required."
#endif
#if (UMB_ENABLE_TRANSPORT || UMB_ENABLE_SENSORS) && !UMB_BOARD_CONFIGURED
#error "Configure reviewed STM32 board pins before enabling any peripheral."
#endif
#if UMB_BOARD_CONFIGURED && !defined(UMB_ROLE_ENABLE_PIN)
#error "Define the active-low UMB_ROLE_ENABLE_PIN for this controller."
#endif
#if UMB_ENABLE_TRANSPORT && (!defined(UMB_UART_RX_PIN) || !defined(UMB_UART_TX_PIN))
#error "Define reviewed STM32 USART RX/TX pins; UMB electrical adapter still required."
#endif
#if UMB_ENABLE_SENSORS && (!defined(UMB_I2C_SDA_PIN) || !defined(UMB_I2C_SCL_PIN))
#error "Define reviewed STM32 I2C SDA/SCL pins and 3.3 V pullups."
#endif

// No bootstrap, flash programming, chain reset/gating, PWM or motor driver
// is implemented here. Enabling UART permits OPERATIONAL BENCH packets only.
