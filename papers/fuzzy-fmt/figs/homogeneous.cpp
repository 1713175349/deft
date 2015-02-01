// Deft is a density functional package developed by the research
// group of Professor David Roundy
//
// Copyright 2010 The Deft Authors
//
// Deft is free software; you can redistribute it and/or modify it
// under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// You should have received a copy of the GNU General Public License
// along with deft; if not, write to the Free Software Foundation,
// Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
//
// Please see the file AUTHORS for a list of authors.

#include <stdio.h>
#include <time.h>
#include "HardFluidFast.h"
#include "SoftFluidFast.h"
#include "equation-of-state.h"
#include "utilities.h"
#include "handymath.h"

// The following tells fac how to run the executable to generate a
// homogeneous.dat file.
/*--

self.rule(exe, [exe], [os.path.dirname(exe)+'/homogeneous.dat'])

--*/

int main(int, char **) {
  double radius = 1.0;
  double sigma = radius*pow(2,5.0/6.0);
  FILE *out = fopen("papers/fuzzy-fmt/figs/homogeneous.dat", "w");
  const double Tmax = 10.0, dT = 0.01, Tmin = dT;
  fprintf(out, "# n_reduced");
  for (double T = Tmin; T<= Tmax + dT/2; T += dT) {
    fprintf(out, "\tp(kT=%g)/nkT", T);
  }
  fprintf(out, "\n0");
  for (double T = Tmin; T<= Tmax + dT/2; T += dT) {
    fprintf(out, "\t%g", T);
  }
  fprintf(out, "\n");

  const double dn = 0.01, nmax = 2.5;
  for (double n_reduced = dn/2; n_reduced <= nmax; n_reduced += dn) {
    fprintf(out, "%g", n_reduced);
    for (double T = Tmin; T<= Tmax + dT/2; T += dT) {
      const double temp = T;
      Functional f = HardFluid(radius,0);
      if (temp > 0) f = SoftFluid(sigma, 1, 0);
      double usekT = temp;
      if (temp == 0) usekT = 1.0;
      const double n = n_reduced*pow(2,-5.0/2.0);
      fprintf(out, "\t%g", pressure(OfEffectivePotential(f), usekT, n));
    }
    fprintf(out, "\n");
  }
  fclose(out);
  return 0;
}
