fn fac(x: i32) i32 {
  if (x == 1) {
    return 1;
  }
  return x * fac(x-1);
}

fn main() void {
  var x_2:i32 = fac(4);
  printf(x_2);
}