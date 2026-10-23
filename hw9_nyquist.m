N = 2001;
Omega = linspace(0, 2*pi, N);
z = exp(1i*Omega(2:N-1)); % exclude omega = 0, 2pi for poles on unit circle

% H = (z)./((z-1).*(z-0.5));
K = 1;
%H = K*(z+0.2).*(z+0.5)./((z-1).*(z-0.5));
% H = (z)./((z-1).*(z.^2-z+0.5));
H= K*(( z - 0.5 ) ./ ( z - 1 ) ) .* ( ( z + 0.95) ./ ( z.^2 - 1.3* z + 0.42 ) ) ;

plot(real(H), imag(H))

% xlim([-9, 1])
% ylim([-3, 3])

hold on
plot(-1, 0, 'o')
hold off