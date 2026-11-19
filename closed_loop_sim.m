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

% lead compensator
Dlead = tf([1, -0.85], [1, -0.72], T);
% Klead = 18;

% zero-placement
target_bandwidth = 4.5;
lag_zero = 1 - rad2deg(target_bandwidth*T)/500;
lag_zero = 0.85;
target_dc_loop_gain = 99;
p = 1 - (1 - lag_zero)*dcgain(Dlead)*dcgain(G)/target_dc_loop_gain
K = 40
Dlag = K*tf([1, -lag_zero], [1, -p], T);

Dlag*Dlead

figure(3)
bode(Dlead*G);
figure(4)

figure(5)
bode(Dlead*G);
figure(6)
step(Dlead*G/(1 + Dlead*G));

figure(7)
bode(Dlag*Dlead*G);
figure(8)
step(Dlag*Dlead*G/(1 + Dlag*Dlead*G));
