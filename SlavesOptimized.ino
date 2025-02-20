#include <EEPROM.h>
#include <SimpleModbusSlave.h>

#define DE_RE_PIN 9
#define PULSE_PIN 11
#define LED_PIN 13
#define SLAVE_ID 2
#define EEPROM_INTERVAL 30000 // update address after this writing is done

enum {
  EsetValueHigh, //0
  EsetValueLow, //1
  pulseCountHigh, //2
  pulseCountLow,  //3
  modifier, //4
  reset, //5
  demandHigh,//6
  demandLow, //7
  setSetHigh,//8
  setSetLow,//9
  prevPulseCountH, //10
  prevPulseCountL, //11
  TOTAL_REGISTERS
};

unsigned int holdingRegs[TOTAL_REGISTERS] = {0};  // Initialize holding registers
unsigned long setV , EsetV , demand = 0;
unsigned long pulseCount = 0, prevPulseCount = 0, writeCount = 1;
uint16_t setValueAddress = 4, writeCountAddress = 518, flagAddress = 360;
bool flag = 0 ; ///change to uin8_t if it does not work
bool currentState = 0, prevState = 0;

void split_ulong(unsigned long value, unsigned int &high, unsigned int &low) {
  low = (unsigned int)(value & 0xFFFF);
  high = (unsigned int)((value >> 16) & 0xFFFF);
}

inline void pulse() {
  currentState = digitalRead(PULSE_PIN);
  if (currentState && !prevState) {  // Only increment on rising edge
    pulseCount++;
  }
  prevState = currentState;
}

inline void updateEEPROM() {
  writeCount++;
  EEPROM.put(writeCountAddress, writeCount);
  EEPROM.put(setValueAddress, setV);
  EEPROM.put(flagAddress, flag );
  
}

void reset_count() { prevPulseCount = pulseCount; pulseCount = 0;} 

void day_rst() {
  pulseCount = 0;
  prevPulseCount = 0;
  writeCount++;
  updateEEPROM();
}

void updateSetValue(bool multiplier) {
  if(holdingRegs[setSetLow] || holdingRegs[setSetHigh]){
  EsetV = holdingRegs[setSetHigh] * 65536 + holdingRegs[setSetLow];
  setV = multiplier ? 3 * EsetV : EsetV;
  flag = multiplier ? 1:0;
  demand = 0;
  EEPROM.put(setValueAddress, setV);
  EEPROM.put(flagAddress, flag );
  writeCount++;
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(DE_RE_PIN, OUTPUT);
  digitalWrite(DE_RE_PIN, LOW);
  pinMode(PULSE_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  modbus_configure(&Serial, 19200, SERIAL_8N1, SLAVE_ID, DE_RE_PIN, TOTAL_REGISTERS, holdingRegs);

  EEPROM.get(516, writeCountAddress);
  EEPROM.get(514, setValueAddress);
  EEPROM.get(setValueAddress + 360, flagAddress);
  EEPROM.get(writeCountAddress, writeCount); // fetching write count
  EEPROM.get(setValueAddress, setV);        // fetching setV
  EEPROM.get(flagAddress , flag);
  EsetV = flag ? 0.3 * setV : setV;  /// ahah secret
  delay(500);

}

void loop() {
  modbus_update();
  pulse();

  // LED Control: Check pulse count against threshold
  digitalWrite(LED_PIN, (pulseCount > setV + demand) ? LOW : HIGH);

  // Modifier-based actions
  switch (holdingRegs[modifier]) {
    case 1: updateSetValue(false); break;
    case 2: updateSetValue(true); break; //multiplied
    case 3:  // Update demand
      demand = (holdingRegs[demandHigh] * 65536 + holdingRegs[demandLow]); //6,7
      break;
    case 4: reset_count(); holdingRegs[modifier] = 0; break;
    case 5: day_rst(); holdingRegs[modifier] = 0; break;
    default:  // No valid modifier, updating registers with EsetV + demand
      split_ulong((EsetV + demand), holdingRegs[EsetValueHigh], holdingRegs[EsetValueLow]);
      break;
  }

  // Update pulse count difference
  split_ulong(pulseCount, holdingRegs[pulseCountHigh], holdingRegs[pulseCountLow]);
  split_ulong(prevPulseCount, holdingRegs[prevPulseCountH], holdingRegs[prevPulseCountL]);

  // Increment EEPROM addresses after interval
  if (writeCount % EEPROM_INTERVAL == 0) {
    setValueAddress = (setValueAddress > 359) ? 0 : setValueAddress + 4; /// 0 to 359 set value address range
    flagAddress = (flagAddress > 513) ? 360 : flagAddress + 4; //// 360 to 513 flag range
    writeCountAddress = (writeCountAddress > 1022) ? 518 : writeCountAddress + 4; /// 518 to 1022 writecount range
  }
}
