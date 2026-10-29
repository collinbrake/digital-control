K = 1;
z = tf('z');
Ha = K*(z)/((z-1)*(z-0.5));
Hb = K*(z+0.2)*(z+0.5)/((z-1)*(z-0.5));
Hc = K*(z)/((z-1)*(z^2-z+0.5));
Hd = K*(z+0.2)*(z+0.5)/((z-1)*(z^2-z+0.5));

% K*(( z - 0.5 ) / ( z - 1 ) ) * ( ( z + 0.95) / ( z^2 - 1.3* z + 0.42 ) ) ;

figure(1)
subplot(2, 1, 1)
rlocus(Ha)
subplot(2, 1, 2)
nyquist(Ha)
sgtitle("Digital Control HW9 1A")

figure(2)
subplot(2, 1, 1)
rlocus(Hb)
subplot(2, 1, 2)
nyquist(Hb)
sgtitle("Digital Control HW9 1B")

figure(3)
subplot(2, 1, 1)
rlocus(Hc)
subplot(2, 1, 2)
nyquist(Hc)
sgtitle("Digital Control HW9 1C")

figure(4)
subplot(2, 1, 1)
rlocus(Hd)
subplot(2, 1, 2)
nyquist(Hd)
sgtitle("Digital Control HW9 1D")