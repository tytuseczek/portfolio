#include <LiquidCrystal.h> //Dołączenie bilbioteki
LiquidCrystal lcd(2, 3, 4, 9, 6, 7); //Informacja o podłączeniu nowego wyświetlacza

int speakerPin = 5;
int length = 28; // the number of notes
char notes[] = "GGAGcB GGAGdc GGxecBA ffecdc";
int beats[] = { 2, 2, 8, 8, 8, 16, 1, 2, 2, 8, 8,8, 16, 1, 2,2,8,8,8,8,16, 1,2,2,8,8,8,16 };
int tempo = 150;

void playTone(int tone, int duration) {
  for (long i = 0; i < duration * 1000L; i += tone * 2) {
    digitalWrite(speakerPin, HIGH);
    delayMicroseconds(tone);
    digitalWrite(speakerPin, LOW);
    delayMicroseconds(tone);
  }
}

void playNote(char note, int duration) {
  char names[] =  {'C',    'D',  'E',  'F',  'G',  'A',  'B', 'c', 'd',  'e',  'f',  'g',  'a',  'b',  'x', 'y' };
  int tones[] =   { 1915, 1700, 1519, 1432, 1275, 1136, 1014, 956,  834,  765,  593,  468,  346,  224, 655 , 715 };
  int frequencies[]={262,  294, 330 ,  349, 392 , 440 ,  494, 523,  587,  659,  698,  784,  880,  988, 831 , 701};
  int SPEE = 5;
  // play the tone corresponding to the note name
  for (int i = 0; i < 16; i++) {
    if (names[i] == note) {
      int newduration = duration/SPEE;
      playTone(tones[i], newduration);
    }
  }
}


void playSong(){
  for (int i = 0; i < length; i++) {
    if (notes[i] == ' ') {
      delay(beats[i] * tempo); // rest
    } else {
      playNote(notes[i], beats[i] * tempo);
      }
   // pause between notes
   delay(tempo);
   }  
}

void setupLCD(){
  lcd.begin(16, 2); //Deklaracja typu
  lcd.setCursor(0, 0); //Ustawienie kursora
  lcd.print("Wszystkiego"); //Wyświetlenie tekstu
  lcd.setCursor(0, 1); //Ustawienie kursora
  lcd.print("Dobrego Jasiu"); //Wyświetlenie tekstu  
}



void setup() {
  setupLCD();
  //Serial.begin(9600);
  //Serial.write("write this");
  pinMode(speakerPin, OUTPUT);


}
 
void loop() {
    playSong();
}
