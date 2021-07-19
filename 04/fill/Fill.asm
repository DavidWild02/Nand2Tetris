// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(INFINITYLOOP)

    @SCREEN
    D=A
    @i
    M=D

    @KBD
    D=M
    @WHITE
    D;JEQ

    (BLACK)
        @COLOUR
        M=-1
        @COLOURINGLOOP
        0;JEQ

    (WHITE)
        @COLOUR
        M=0

    (COLOURINGLOOP)
        @COLOUR
        D=M
        @i
        A=M
        M=D

        // inc i
        D=A+1
        @i
        M=D

        @KBD
        D=A-D
        @COLOURINGLOOP
        D;JGT
        

    @INFINITYLOOP
    0;JEQ