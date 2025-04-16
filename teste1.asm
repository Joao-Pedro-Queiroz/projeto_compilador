section .data
   format_out db "%d", 10, 0
   format_in db "%d", 0
   scan_int dd 0

section .text

   extern printf
   extern scanf
   extern _ExitProcess@4
   global _start

_start:
   push ebp
   mov ebp, esp

   sub esp, 4 ; reserva espaço para x
   sub esp, 4 ; reserva espaço para y
   mov eax, 1
   neg eax
   push eax
   mov eax, 3
   pop ecx
   add eax, ecx
   mov [ebp-4], eax
   mov eax, [ebp-4]
   mov [ebp-8], eax
   mov eax, 5
   push eax
   mov eax, [ebp-4]
   pop ecx
   cmp eax, ecx
   mov eax, 0
   mov ecx, 1
   cmovl eax, ecx
   push eax
   mov eax, 1
   push eax
   mov eax, [ebp-4]
   pop ecx
   cmp eax, ecx
   mov eax, 0
   mov ecx, 1
   cmovg eax, ecx
   pop ecx
   test eax, eax
   jne true_or
   test ecx, ecx
   jne true_or
   mov eax, 0
   jmp end_or
   true_or:
   mov eax, 1
   end_or:
   cmp eax, 0
   je endif_29
   mov eax, 1
   push eax
   mov eax, 5
   pop ecx
   sub eax, ecx
   mov [ebp-4], eax
   endif_29:
   mov eax, 3
   push eax
   mov eax, [ebp-8]
   pop ecx
   cmp eax, ecx
   mov eax, 0
   mov ecx, 1
   cmove eax, ecx
   push eax
   mov eax, 3
   push eax
   mov eax, [ebp-4]
   pop ecx
   cmp eax, ecx
   mov eax, 0
   mov ecx, 1
   cmove eax, ecx
   pop ecx
   test eax, eax
   je false_and
   test ecx, ecx
   je false_and
   mov eax, 1
   jmp end_and
   false_and:
   mov eax, 0
   end_and:
   cmp eax, 0
   je else_42
   jmp endif_42
   else_42:
   mov eax, 3
   mov [ebp-4], eax
   endif_42:
   mov eax, 3
   mov [ebp-4], eax
   loop_60:
   mov eax, 5
   push eax
   mov eax, [ebp-4]
   pop ecx
   cmp eax, ecx
   mov eax, 0
   mov ecx, 1
   cmovl eax, ecx
   cmp eax, 0
   je exit_60
   mov eax, 1
   push eax
   mov eax, [ebp-4]
   pop ecx
   sub eax, ecx
   mov [ebp-8], eax
   mov eax, 1
   push eax
   mov eax, [ebp-4]
   pop ecx
   add eax, ecx
   mov [ebp-4], eax
   jmp loop_60
   exit_60:
   mov eax, [ebp-4]
   push eax
   push format_out
   call printf
   add esp, 8

   mov esp, ebp
   pop ebp

   mov eax, 1
   xor ebx, ebx
   int 0x80
