# NUBI Index Protocol
# Topics: /status_command (PC -> STM)  |  /status_response (STM -> PC)
# Message type: std_msgs/Int16MultiArray, fixed size = 41 elements
# data[0] = index  |  data[1..40] = payload  |  unused bytes = 0

## PC -> STM  (/status_command)

INDEX  ACTION                  PAYLOAD
-----  ------                  -------
  0    Request status array    (none)   STM reads all 20 servo status registers
                                        and replies with index 1
  2    Torque set              data[1]: 1 = torqueON(BROADCAST)
                                        0 = torqueOFF(BROADCAST)
  3    Request torque array    (none)   STM reads all 20 servo torque registers
                                        and replies with index 5
  6    Reset error             (none)   STM calls clearError(BROADCAST_ID)
  7    Reinitialize servos     (none)   STM reboots all 20 servos (50ms each),
                                        waits 1500ms, then runs initialize()
                                        (clearError + ACK(1) + torqueON) plus
                                        a second clearError+torqueON pass
  8    Move one servo          data[1]: servo_id (0-19)
                                data[2]: angle in degrees (int16, -160..160)
                                data[3]: play_time in ms (0-2856)

## STM -> PC  (/status_response)

INDEX  MEANING                 PAYLOAD
-----  -------                 -------
  1    Status array            data[1..40] = 20 x [statusError, statusDetail]
                                  data[1]  = servo 0 statusError
                                  data[2]  = servo 0 statusDetail
                                  data[3]  = servo 1 statusError
                                  data[4]  = servo 1 statusDetail
                                  ... (2 bytes per servo, 20 servos = 40 bytes)
  5    Torque array            data[1..20] = 20 x torque byte
                                  data[1]  = servo 0  (1=ON, 0=OFF)
                                  data[2]  = servo 1
                                  ... (1 byte per servo, 20 servos = 20 bytes)

## Notes

- All arrays are padded with zeros to STATUS_ARRAY_SIZE = 41
- The nubi_debug (/nubi_debug, std_msgs/String) prints the received index and
  indicated action for every status_command received, plus timing info for
  status and torque read operations
- Torque toggle from the GUI triggers 5 consecutive torque status polls
  (index 3 sent once per second for 5 seconds) to verify the change
- Status and torque data are on-demand only; there are no periodic timers
  publishing them autonomously on the STM
