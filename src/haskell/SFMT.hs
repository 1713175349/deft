{- SFMT defines the fundamental measures that are the raw input of
soft fundamental measure theory. -}

module SFMT
       ( sfmt, sfmt_fluid_n, sfmt_fluid_Veff, homogeneous_sfmt_fluid,
         phi1, phi2, phi3,
         n0, n1, n2, n3, n2v, n1v, sqr_n2v, n1v_dot_n2v )
       where

import Expression
import IdealGas ( kT, idealgas )

phi1, phi2, phi3 :: Expression Scalar
phi1 = var "phi1" "\\Phi_1" $ integrate $ -kT*n0*log(1-n3)
phi2 = var "phi2" "\\Phi_2" $ integrate $ kT*(n2*n1 - n1v_dot_n2v)/(1-n3)
-- The following was Rosenfelds early vector version of the functional
-- phi3 = var "phi3" "\\Phi_3" $ integrate $ kT*(n2**3/3 - sqr_n2v*n2)/(8*pi*(1-n3)**2)

-- This is the fixed version, which comes from dimensional crossover
phi3 = var "phi3" "\\Phi_3" $ integrate $ kT*n2**3*(1 - sqr_n2v/n2**2)**3/(24*pi*(1-n3)**2)

sfmt :: Expression Scalar
sfmt = var "sfmt" "F_{\\text{soft}}" $ (phi1 + phi2 + phi3)

sfmt_fluid_n :: Expression Scalar
sfmt_fluid_n = substitute n (r_var "n") $
               sfmt + idealgas + ("external" === integrate (n * (r_var "Vext" - s_var "mu")))

sfmt_fluid_Veff :: Expression Scalar
sfmt_fluid_Veff = substitute n ("n" === exp(- r_var "Veff"/kT)) $
                  sfmt + idealgas + ("external" === integrate (n * (r_var "Vext" - s_var "mu")))

homogeneous_sfmt_fluid :: Expression Scalar
homogeneous_sfmt_fluid = makeHomogeneous $ substitute n (r_var "n") $
                         sfmt + idealgas - integrate (n * s_var "mu")

sigma :: Type a => Expression a
sigma = s_var "sigma"

betaeps :: Type a => Expression a
betaeps = s_var "epsilon"/kT

xi :: Type a => Expression a
xi = scalar $ var "Xi" "\\Xi" (alpha/(6*sqrt(pi)*(sqrt(betaeps * log 2 ) + log 2)))

alpha :: Type a => Expression a
alpha = scalar $ var "alpha" "\\alpha" (sigma*(2/(1+sqrt(log 2 / betaeps)))**(1.0/6.0))

n, n3, n2, n1, n0, n1v_dot_n2v, sqr_n2v :: Expression RealSpace
n = "n" === r_var "x"
n3 = "n3" === w3 n
n2 = "n2" === w2 n
n1 = "n1" === w1 n
n0 = "n0" === w0 n

n2v, n1v :: Vector RealSpace
n2v = "n2v" `nameVector` w2v n
n1v = "n1v" `nameVector` w1v n

sqr_n2v = var "n2vsqr" "{\\left|\\vec{n}_{2v}\\right|^2}" (n2v `dot` n2v)
n1v_dot_n2v = var "n1v_dot_n2v" "{\\vec{n}_{1v}\\cdot\\vec{n}_{2v}}" (n2v `dot` n1v)


w3 :: Expression RealSpace -> Expression RealSpace
w3 x = ifft ( w3k * fft x)
  where w3k = var "w3k" "\\tilde{w_3}(k)" $
              4*pi/(k**2)*exp(-((xi/sqrt 2)*k/2)**2)*((1+(xi/sqrt 2)**2*k**2/2)*sin kalphao2/k - alpha/2*cos kalphao2)
        kalphao2 = k*alpha/2

w1 :: Expression RealSpace -> Expression RealSpace
w1 x = ifft ( w1k * fft x)
  where w1k = var "w1k" "\\tilde{w_1}(k)" $
              1/k*exp(-((xi/sqrt 2)*k/2)**2)*sin(k*alpha/2)

w0 :: Expression RealSpace -> Expression RealSpace
w0 x = ifft ( w0k * fft x)
  where w0k = var "w0k" "\\tilde{w_0}(k)" $
              (sqrt (pi/2)/(k*xi)) *exp(-0.5*alpha**2/xi**2)*(real_part_complex_erf(k*xi/2/sqrt 2 + imaginary*alpha/sqrt 2/xi))

w2 :: Expression RealSpace -> Expression RealSpace
w2 x = ifft ( w2k * fft x)
  where w2k = var "w2k" "\\tilde{w_2}(k)" $
              2*pi*exp(-((xi/sqrt 2)*k/2)**2)*((xi/sqrt 2)**2*cos(k*alpha/2) + alpha*sin(k*alpha/2)/k)

w2v :: Expression RealSpace -> Vector RealSpace
w2v x = vector_convolve w2vk x
  where w2vk = kvec *. (imaginary * pi*exp(-((xi/sqrt 2)*k/2)**2)*((alpha**2-(xi/sqrt 2)**4*k**2)*cos(k*alpha/2)-
                                               2*alpha*((xi/sqrt 2)**2*k+1/k)*sin(k*alpha/2))/k**2)

w1v :: Expression RealSpace -> Vector RealSpace
w1v x = vector_convolve w1vk x
  where w1vk = kvec *. (imaginary * exp(-((xi/sqrt 2)*k/2)**2)*(alpha/2*cos(k*alpha/2)-((xi/sqrt 2)**2*k/2+1/k)*sin(k*alpha/2))/k**2)

w2xx :: Expression RealSpace -> Expression RealSpace
w2xx x = ifft ( w2xxk * fft x)
  where w2xxk = var "w2xxk" "\\tilde{w_{2xx}}(k)" $
              (4*pi*exp(-(xi*k)**2/8)*((xi/sqrt 2/k/3 - 1/k**2)*cos(k*alpha/2) + xi*alpha/(12*sqrt 2)*sin(k*alpha/2))
                +
                (2*pi)**(3/2)/k**3/xi*exp(-alpha**2/2/xi**2)*
                2*real_part_complex_erf(k*xi/2**1.5 + imaginary*alpha/sqrt 2/xi)
              )
