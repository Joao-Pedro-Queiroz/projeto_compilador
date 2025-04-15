section .data
  format_out: db "%d", 10, 0 ; format do printf
  format_in: db "%d", 0 ; format do scanf
  scan_int: dd 0; 32-bits integer`

section .text

  extern printf ; usar _printf para Windows
  extern scanf ; usar _scanf para Windows
  ; extern _ExitProcess@4 ; usar para Windows
  global _start ; início do programa

_start:
  push ebp ; guarda o EBP
  mov ebp, esp ; zera a pilha

  ; aqui começa o codigo gerado:

  mov eax, 3

  push eax ; empilha eax
  push format_out ; formato int de saida
  call printf ; Print f
  add esp, 8 ; limpa os argumentos

  ; aqui termina o código gerado

  mov esp, ebp ; reestabelece a pilha
  pop ebp

  ; chamada da interrupcao de saida (Linux)
  mov eax, 1   
  xor ebx, ebx 
  int 0x80     
  ; Para Windows:
  ; push dword 0        
  ; call _ExitProcess@4