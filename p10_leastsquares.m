function [A, X] = leastsquares(x, f)
    X = [x.^0, x.^1, x.^2, x.^3, x.^4, x.^5, x.^6, x.^7];
    A = inv(X'*X)*X'*f;
end

function [A, X] = leastsquares10(x, f)
    X = [x.^0, x.^1, x.^2, x.^3, x.^4, x.^5, x.^6, x.^7, x.^8];
    A = inv(X'*X)*X'*f;
end

% 7th-order least squares approximation with 99 fitting points
x = [0:pi/98:pi]';
f = cos(2*cos(2*cos(x')))';
[A1, X1] = leastsquares(x, f);

% 7th-order least squares approximation with 999 fitting points
x2 = [0:pi/998:pi]';
f2 = cos(2*cos(2*cos(x2')))';
[A2, X2] = leastsquares(x2, f2);

% 8th-order least squares approximation with 99 fitting points
[A3, X3] = leastsquares10(x, f);

rms1 = sqrt(sum((f - X1*A1).^2)/length(f))
rms2 = sqrt(sum((f2 - X2*A2).^2)/length(f2))
rms3 = sqrt(sum((f - X3*A3).^2)/length(f))

plot(x,  f,      ...
     x,  X1*A1,  ...
     x,  X3*A3,  ...
     x2, X2*A2)
legend('Original (99 points)', ...
       'LS Fit (99 points)', ...
       'LS Fit (8th order (99 points)', ...
       'LS Fit (999 points)')
grid on