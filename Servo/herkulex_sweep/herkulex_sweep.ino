/*
 * herkulex_sweep.ino
 *
 * Sweeps a single Herkulex DRS-0101 servo across its full ±160° range.
 * Debug output is published to the /nubi_debug ROS topic (std_msgs/String),
 * identical to the STM_microROS firmware pattern.
 *
 * On error: backs off BACKOFF_DEG in the opposite direction, clears the
 * latched fault, re-enables torque, then resumes sweeping.
 *
 * Wiring (STM32 Black Pill / Blue Pill):
 *   STM32 PA9  (TX) → Servo SIGNAL RX
 *   STM32 PA10 (RX) ← Servo SIGNAL TX   (separate lines, not half-duplex)
 *   Servo PWR  → 7.4–8.4V
 *   Servo GND  → Common GND with STM32
 */

#include <micro_ros_arduino.h>
#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <std_msgs/msg/string.h>
#include <string.h>
#include "Herkulex.h"

// ────────────────────────────────────────────────────────────────────────────
// CONFIGURE ME
// ────────────────────────────────────────────────────────────────────────────
#define SERVO_ID        2       // servo's programmed ID
#define SWEEP_MIN    -50.0f    // degrees (library clips at ±160 internally)
#define SWEEP_MAX     50.0f    // degrees
#define STEP_DEG        5.0f    // degrees per step
#define STEP_TIME_MS    400     // ms given to the servo to reach each step
#define BACKOFF_DEG    10.0f    // degrees to retreat on error before continuing
// ────────────────────────────────────────────────────────────────────────────

#define SERVO_RX_PIN  PA10
#define SERVO_TX_PIN  PA9

// ── micro-ROS objects ────────────────────────────────────────────────────────
rclc_support_t   support;
rcl_allocator_t  allocator;
rcl_node_t       node;
rcl_publisher_t  debug_publisher;
rclc_executor_t  executor;

std_msgs__msg__String debug_msg;
static char _dbuf[128];

// ftoa: convert float to 1-decimal string — works on newlib-nano (no %f in snprintf)
static char _ftoa_bufs[4][16];  // 4 independent slots for use in one snprintf
static int  _ftoa_slot = 0;
const char* ftoa(float v) {
  int slot = _ftoa_slot++ & 0x03;
  int whole = (int)v;
  int frac  = (int)((v - whole) * 10);
  if (frac < 0) frac = -frac;
  snprintf(_ftoa_bufs[slot], sizeof(_ftoa_bufs[slot]), "%d.%d", whole, frac);
  return _ftoa_bufs[slot];
}

// ── debug_log: publish to /nubi_debug exactly as STM_microROS does ───────────
void debug_log(const char* msg) {
  debug_msg.data.data     = _dbuf;
  debug_msg.data.capacity = sizeof(_dbuf);
  strncpy(_dbuf, msg, sizeof(_dbuf) - 1);
  _dbuf[sizeof(_dbuf) - 1] = '\0';
  debug_msg.data.size = strlen(_dbuf);
  rcl_publish(&debug_publisher, &debug_msg, NULL);
}

float current_angle = SWEEP_MIN;
int   direction     = 1;   // +1 toward SWEEP_MAX, -1 toward SWEEP_MIN

// ── helpers ──────────────────────────────────────────────────────────────────

void servo_init() {
  Herkulex.begin(115200, SERVO_RX_PIN, SERVO_TX_PIN);
  delay(500);

  Herkulex.clearError(SERVO_ID);
  delay(10);
  Herkulex.ACK(1);
  delay(10);
  Herkulex.torqueON(SERVO_ID);
  delay(50);

  debug_log("[sweep] servo initialised, torque ON");
}

void move_to(float angle, int time_ms) {
  snprintf(_dbuf, sizeof(_dbuf), "[sweep] >> cmd=%s deg  time=%dms", ftoa(angle), time_ms);
  debug_log(_dbuf);

  Herkulex.clearError(SERVO_ID);
  Herkulex.moveOneAngle(SERVO_ID, angle, time_ms, LED_GREEN);
  delay(time_ms + 50);

  float actual = Herkulex.getAngle(SERVO_ID);
  byte  statusError, statusDetail;
  Herkulex.stat(SERVO_ID, statusError, statusDetail);

  snprintf(_dbuf, sizeof(_dbuf),
           "[sweep] actual=%s deg  err=0x%02X  detail=0x%02X",
           ftoa(actual), statusError, statusDetail);
  debug_log(_dbuf);

  if (statusError != 0x00) {
    // ── ERROR RECOVERY: back off, clear latch, re-enable torque ───────────
    float backoff = current_angle - (direction * BACKOFF_DEG);
    // clamp backoff to within sweep range
    if (backoff > SWEEP_MAX) backoff = SWEEP_MAX;
    if (backoff < SWEEP_MIN) backoff = SWEEP_MIN;

    snprintf(_dbuf, sizeof(_dbuf),
             "[sweep] ERROR 0x%02X — backing off to %s deg then resuming",
             statusError, ftoa(backoff));
    debug_log(_dbuf);

    Herkulex.clearError(SERVO_ID);
    delay(10);
    Herkulex.torqueON(SERVO_ID);
    delay(20);

    Herkulex.moveOneAngle(SERVO_ID, backoff, time_ms, LED_RED);
    delay(time_ms + 50);

    // Update current_angle to the backoff position so the sweep
    // continues from here without jumping
    current_angle = backoff;
    debug_log("[sweep] backoff done, resuming sweep");
  }

  // spin executor to flush any pending publish
  rclc_executor_spin_some(&executor, RCL_MS_TO_NS(2));
}

// ── Arduino entry points ──────────────────────────────────────────────────────

void setup() {
  set_microros_transports();
  delay(2000);

  allocator = rcl_get_default_allocator();
  rclc_support_init(&support, 0, NULL, &allocator);
  rclc_node_init_default(&node, "nubi_sweep_node", "", &support);

  rclc_publisher_init_default(
    &debug_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, String),
    "nubi_debug");

  rclc_executor_init(&executor, &support.context, 1, &allocator);

  snprintf(_dbuf, sizeof(_dbuf),
           "[sweep] START  ID=%d  range=%s..%s deg  step=%s deg  backoff=%s deg",
           SERVO_ID, ftoa(SWEEP_MIN), ftoa(SWEEP_MAX), ftoa(STEP_DEG), ftoa(BACKOFF_DEG));
  debug_log(_dbuf);

  servo_init();

  move_to(SWEEP_MIN, 1500);
  current_angle = SWEEP_MIN;
}

void loop() {
  move_to(current_angle, STEP_TIME_MS);

  current_angle += direction * STEP_DEG;

  if (current_angle >= SWEEP_MAX) {
    current_angle = SWEEP_MAX;
    direction = -1;
    debug_log("[sweep] --- reached MAX, reversing ---");
  } else if (current_angle <= SWEEP_MIN) {
    current_angle = SWEEP_MIN;
    direction = +1;
    debug_log("[sweep] --- reached MIN, reversing ---");
  }
}
