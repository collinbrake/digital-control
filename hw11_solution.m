p=0.5;
tfinal=1;
T = 0.025;

b2 = 0;
b1 = 0.002296;
b0 = 0.002288;
a1= -1.952;
a0 = 0.9902;


%custom

a1 = -1.92894;
a0 = 0.946607;
b1 = 0.00998879;
b0 = -0.00861729;

KF = ((1-p)^2)/0.00458;
fb2 = KF;
fb1 = -1.952*KF;
fb0= 0.9902*KF;
fa1 = -2*p;
fa0 = p^2;

tvec=[-2*T:T:tfinal];
N=length(tvec);
r=ones(1,N);
r(1)=0;
r(2)=0;
u=zeros(1,N);
y=zeros(1,N);
yunc=zeros(1,N);

for k=1:N-2
    yunc(k+2) = -a1*yunc(k+1)-a0*yunc(k)+b2*r(k+2)+b1*r(k+1)+b0*r(k);
    u(k+2) = -fa1*u(k+1)-fa0*u(k) + fb2*r(k+2) + fb1*r(k+1)+fb0*r(k);
    y(k+2) = -a1*y(k+1)-a0*y(k)+b2*u(k+2)+b1*u(k+1)+b0*u(k);
end

figure(1)
stairs(tvec,yunc,'r')
hold on
stairs(tvec,y,'k')
hold off

figure(2)
plot(tvec,u)
