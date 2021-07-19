// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
//
// This program only needs to handle arguments that satisfy
// R0 >= 0, R1 >= 0, and R0*R1 < 32768.

//    product = R0
//    n = R1 + 1
//
//    while true:
//        n--
//        break if n <= 0 
//        product += n
//    
//    R2 = product

@R0
D=M
@factor
M=D

@R1
D=M
@n
M=D+1

@product
M=0

(LOOP)
    @n
    M=M-1
    D=M
    @STOP
    D;JEQ

    @factor
    D=M
    @product
    M=M+D

    @LOOP
    0;JEQ

(STOP)
    @product
    D=M
    @R2
    M=D

@25
0;JEQ