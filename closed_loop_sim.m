% closed_loop_sim.m
% Lead-lag compensator D(z) for the README model G(z), T = 50 ms.
%
% Changes from the previous version:
%   1. The lead gain comes from the target crossover (evalfr) instead of a
%      hand-picked K, and the lag-pole formula includes the gain, so the DC
%      loop gain really is target_dc_loop_gain. (Before: K = 40 was applied
%      in Dlag and left out of the pole formula, so the DC loop gain came out
%      40*99 = 3960 and crossover moved to 8.2 rad/s.)
%   2. Margins come from margin() and closed loops from feedback(), so the
%      script reports PM / crossover / settling instead of relying on plots.
%   3. Every design is also checked on Gn5, the re-fit of the 2026-11-05
%      hardware data (model_check.py). The lab design (lead pole 0.72, K = 18)
%      has 56 deg of PM on G but about 1 deg on Gn5.
%   4. Final design: lead pole 0.72 -> 0.30, K 18 -> 15, both zeros stay at
%      0.85, lag pole from the same DC-loop-gain rule. PM about 82 deg on G and
%      63 deg on Gn5. It is slower as a stand-alone closed loop (about 5 s),
%      which is fine inside the Bridge-T where F(z) does the fast part
%      (bridge_t_sim.py).
%   5. Prints the difference equation for closed_loop.py with full precision.
%      Rounding 4z^2 - 6.8z + 2.89 to 4z^2 - 6z + 3 made the loop unstable.

clear; close all;
tfinal = 10;
T = 0.05;

% =========================================================
% Plant
% =========================================================

a1 = -1.92894;
a0 = 0.946607;
b1 = 0.00998879;
b0 = -0.00861729;

G = tf([0 b1 b0], [1 a1 a0], T);        % README model (design model)

% Nov 5 re-fit (2-sample delay), in the code's volts: closed_loop.py sends
% val = -u/15*4095, while G was fit with 293 DAC counts per volt
code_scale = (4095/15)/293;
Gn5 = code_scale*tf(0.00237655, [1 -1.90057153 0.94027358], T);

figure(1)
bode(G, Gn5); grid on
legend('G (README model)', 'Gn5 (Nov 5 re-fit)')
title('Plant: design model vs Nov 5 hardware re-fit')

% =========================================================
% Lead compensator
% =========================================================

target_bandwidth = 4.5;                 % rad/s, target crossover
zc = exp(1j*target_bandwidth*T);        % that frequency on the unit circle

Dlead = tf([1 -0.85], [1 -0.72], T);    % about 20 deg of lead at 4.5 rad/s
Klead = 1/abs(evalfr(Dlead*G, zc));     % gain that puts crossover at 4.5 rad/s
[~, pm_lead, ~, wc_lead] = margin(Klead*Dlead*G);
fprintf('Lead only: %.1f deg of lead at %.1f rad/s, Klead = %.1f, PM = %.1f deg at %.2f rad/s\n', ...
    rad2deg(angle(evalfr(Dlead, zc))), target_bandwidth, Klead, pm_lead, wc_lead);

figure(2)
margin(Klead*Dlead*G); grid on

% =========================================================
% Lag compensator
% =========================================================

lag_zero_rule = 1 - rad2deg(target_bandwidth*T)/500;   % rule of thumb, 0.974
lag_zero = 0.85;                                         % chosen for speed

% phase the lag costs at the target crossover (worst case: pole at 1)
fprintf('Lag phase at %.1f rad/s: zero %.3f -> %.1f deg, zero %.2f -> %.1f deg\n', ...
    target_bandwidth, ...
    lag_zero_rule, rad2deg(angle((zc - lag_zero_rule)/(zc - 1))), ...
    lag_zero, rad2deg(angle((zc - lag_zero)/(zc - 1))));

target_dc_loop_gain = 99;               % 1% steady-state error

% lag pole so that K*Dlead(1)*Dlag(1)*G(1) = target_dc_loop_gain (K included)
lag_pole = @(K, Dl) 1 - (1 - lag_zero)*K*dcgain(Dl)*dcgain(G)/target_dc_loop_gain;

% lab design (README): K = 18, lead pole 0.72
K_lab = 18;
p_lab = lag_pole(K_lab, Dlead);
D_lab = K_lab*Dlead*tf([1 -lag_zero], [1 -p_lab], T);

% re-tuned design (bridge_t.py): K = 15, lead pole 0.30
lead_zero = 0.85;
lead_pole = 0.30;
K = 15;
Dlead2 = tf([1 -lead_zero], [1 -lead_pole], T);
p = lag_pole(K, Dlead2);
Dlag = tf([1 -lag_zero], [1 -p], T);
D = K*Dlead2*Dlag

fprintf('\n');
print_margins(sprintf('Lab D: K = %g, lead pole 0.72, lag pole %.5f', K_lab, p_lab), D_lab, G, Gn5);
print_margins(sprintf('Re-tuned D: K = %g, lead pole %.2f, lag pole %.5f', K, lead_pole, p), D, G, Gn5);

% =========================================================
% Plots
% =========================================================

figure(3)
bode(D_lab*G, D_lab*Gn5, D*G, D*Gn5); grid on
legend('lab D \times G', 'lab D \times Gn5', 'D \times G', 'D \times Gn5')
title('Loop gain D(z)G(z)')

figure(4)
margin(D*G); grid on

figure(5)
margin(D*Gn5); grid on

figure(6)
step(feedback(D_lab*G, 1), feedback(D*G, 1), feedback(D*Gn5, 1), tfinal); grid on
legend('lab D, G', 'D, G', 'D, Gn5')
title('Closed-loop step, D alone (no F)')

figure(7)
step(feedback(D_lab*Gn5, 1), tfinal); grid on
title('Lab D on the Nov 5 re-fit')

% =========================================================
% Difference equation for closed_loop.py
% =========================================================

[num, den] = tfdata(D, 'v');
fprintf('\nclosed_loop.py, direct form (keep every digit; r1km1/r1km2 hold e[k-1], e[k-2]):\n');
fprintf('u1 = %.7f*u1km1 %+.7f*u1km2 %+.7f*e %+.7f*r1km1 %+.7f*r1km2\n', ...
    -den(2), -den(3), num(1), num(2), num(3));
fprintf('\nclosed_loop.py, cascade form (zeros stay exact, safer to edit):\n');
fprintf('x  = %.2f*xkm1 + %g*(e - %.2f*ekm1)\n', lead_pole, K, lead_zero);
fprintf('u1 = %.5f*u1km1 + x - %.2f*xkm1\n', p, lag_zero);

% =========================================================
% Local functions
% =========================================================

function print_margins(name, D, G, Gn5)
    fprintf('%s\n', name);
    plants = {G, Gn5};
    labels = {'G  ', 'Gn5'};
    for i = 1:2
        L = D*plants{i};
        [gm, pm, ~, wc] = margin(L);
        cl = feedback(L, 1);
        stable = all(abs(pole(cl)) < 1);
        if stable
            s = stepinfo(cl, 'SettlingTimeThreshold', 0.05);
            ts = s.SettlingTime;
            os = s.Overshoot;
        else
            ts = NaN;
            os = NaN;
        end
        fprintf(['  %s: PM = %5.1f deg at %5.2f rad/s, GM = %5.1f dB, DC loop gain = %5.1f, ' ...
                 'stable = %d, 5%% settling = %5.2f s, overshoot = %4.1f%%\n'], ...
            labels{i}, pm, wc, 20*log10(gm), dcgain(L), stable, ts, os);
    end
end
