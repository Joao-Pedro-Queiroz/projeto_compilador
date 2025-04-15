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

  sub esp, 4 ; var i int [EBP-4]
  sub esp, 4 ; var n int [EBP-8]
  sub esp, 4 ; var f int [EBP-12]

  mov eax, 1
  mov [ebp-12], eax ; f = 1

  push scan_int ; endereço de memória de suporte
  push format_in ; formato de entrada (int)
  call scanf
  add esp, 8 ; Remove os argumentos da pilha

  mov eax, dword [scan_int] ; retorna o valor lido em EAX

  mov [ebp-8], eax ; n = Scan()

  mov eax, 2
  mov [ebp-4], eax ; i = 2

  loop_34: ; label do loop 

  mov eax, 1
  push eax ; empilha 1

  mov eax, [ebp-8] ; recupera n

  pop ecx
  add eax, ecx ; n + 1
  push eax ; empilha n + 1

  ; condicional do loop
  mov eax, [ebp-4]; recupera i

  pop ecx
  cmp eax, ecx
  mov eax, 0
  mov ecx, 1
  cmovl eax, ecx ; i < n + 1

  cmp eax, 0 ; se a condição for falsa, sai
  je exit_34

  ; bloco de comandos
  mov eax, [ebp-4] ; i
  push eax ; empilha i
  mov eax, [ebp-12] ; f
  pop ecx ; desempilha i
  imul ecx ; f * i
  mov [ebp-12], eax ; f = f * i

  ; incremento
  mov eax, 1
  push eax ; empilha 1
  mov eax, [ebp-4]
  pop ecx
  add eax, ecx ; i + 1

  mov [ebp-4], eax ; i = i + 1

  jmp loop_34
  exit_34:

  mov eax, [ebp-12]
  push eax ; empilha f
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