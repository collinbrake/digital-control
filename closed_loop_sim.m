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
Klead = 18;

% zero-placement
target_bandwidth = 4.5;
lag_zero = 1 - rad2deg(target_bandwidth*T)/500;
target_dc_loop_gain = 99;
p = 1 - (1 - lag_zero)*Klead*dcgain(Dlead)*dcgain(G)/target_dc_loop_gain;
Dlag = tf([1, -lag_zero], [1, -p], T);
achieved_dc_loop_gain = dcgain(Klead*Dlag*Dlead*G);
assert(abs(achieved_dc_loop_gain - target_dc_loop_gain) < 1e-8*target_dc_loop_gain, ...
    'Lag compensator pole does not achieve the target DC loop gain.');
fprintf('Lag compensator zero = %.6f, pole p = %.6f\n', lag_zero, p);

figure(3)
bode(Dlead*G);
figure(4)

figure(5)
bode(Klead*Dlead*G);
figure(6)
step(Klead*Dlead*G/(1 + 18*Dlead*G));

figure(7)
bode(Dlag*Klead*Dlead*G);
figure(8)
step(Dlag*Klead*Dlead*G/(1 + Dlag*Klead*Dlead*G));
