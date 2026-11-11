p=0.86;
tfinal=3;
T = 0.05;

a1 = -1.92894;
a0 = 0.946607;
b1 = 0.00998879;
b0 = -0.00861729;

G = tf([0 b1 b0], [1 a1 a0], T);

bode(G);
figure(2)
step(G);

Dlead = tf([1, -0.85], [1, -0.72], T);

figure(3)
bode(Dlead*G);
figure(4)

figure(5)
bode(18*Dlead*G);
figure(6)
step(18*Dlead*G/(1 + 18*Dlead*G));