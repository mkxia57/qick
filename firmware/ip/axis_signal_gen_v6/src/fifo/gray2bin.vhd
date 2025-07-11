library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.MATH_REAL.ALL;
use IEEE.NUMERIC_STD.ALL;

entity gray2bin is
   Generic
   (
      -- Data width.
      B : Integer := 8
   );
   Port
   (
      din   : in std_logic_vector (B-1 downto 0);
      dout: out std_logic_vector (B-1 downto 0)
   );
end gray2bin;

architecture rtl of gray2bin is

signal bin : std_logic_vector (B-1 downto 0);

begin

-- MSB always match.
bin(B-1) <= din(B-1);

GEN: for I in 0 to B-2 generate
begin
   bin(I) <= bin(I+1) xor din(I);
end generate GEN;
   
-- Assign output.
dout <= bin;

end rtl;

