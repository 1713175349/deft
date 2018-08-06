#include <stdlib.h>
#include <float.h>
#include "Monte-Carlo/square-well.h"
#include "handymath.h"
#include <sys/stat.h> // for seeing if the movie data file already exists.

#include "version-identifier.h"

ball::ball(){
  pos = vector3d();
  R = 1;
  neighbors = 0;
  num_neighbors = 0;
  neighbor_center = vector3d();
}

ball::ball(const ball &p){
  pos = p.pos;
  R = p.R;
  neighbors = p.neighbors;
  num_neighbors = p.num_neighbors;
  neighbor_center = p.neighbor_center;
}

ball ball::operator=(const ball &p){
  pos = p.pos;
  R = p.R;
  neighbors = p.neighbors;
  num_neighbors = p.num_neighbors;
  neighbor_center = p.neighbor_center;
  return *this;
}

move_info::move_info(){
  total_old = 0;
  total = 0;
  working = 0;
  working_old = 0;
  updates = 0;
  informs = 0;
}

// Modulates v to within the periodic boundaries of the cell
static inline vector3d sw_fix_periodic(vector3d v, const double len[3]){
  for (int i = 0; i < 3; i++) {
    while (v[i] > len[i]) v[i] -= len[i];
    while (v[i] < 0.0) v[i] += len[i];
  }
  return v;
}

vector3d periodic_diff(const vector3d &a, const vector3d  &b, const double len[3],
                       const int walls){
  vector3d v = b - a;
  // for (int i = walls; i < 3; i++){
  //   if (len[i] > 0){
  //     while (v[i] > len[i]/2.0)
  //       v[i] -= len[i];
  //     while (v[i] < -len[i]/2.0)
  //       v[i] += len[i];
  //   }
  // }
  if (2 >= walls) {
    if (v.z > 0.5*len[2]) v.z -= len[2];
    else if (v.z < -0.5*len[2]) v.z += len[2];
    if (1 >= walls) {
      if (v.y > 0.5*len[1]) v.y -= len[1];
      else if (v.y < -0.5*len[1]) v.y += len[1];
      if (0 >= walls) {
        if (v.x > 0.5*len[0]) v.x -= len[0];
        else if (v.x < -0.5*len[0]) v.x += len[0];
      }
    }
  }
  return v;
}

int initialize_neighbor_tables(ball *p, int N, double neighbor_R, int max_neighbors,
                               const double len[3], int walls){
  int most_neighbors = 0;
  for (int i = 0; i < N; i++){
    p[i].neighbor_center = p[i].pos;
  }
  for(int i = 0; i < N; i++){
    p[i].neighbors = new int[max_neighbors];
    p[i].num_neighbors = 0;
    for (int j = 0; j < N; j++){
      const bool is_neighbor = (i != j) &&
        (periodic_diff(p[i].pos, p[j].pos, len, walls).normsquared() <
         sqr(p[i].R + p[j].R + neighbor_R));
      if (is_neighbor){
        const int index = p[i].num_neighbors;
        p[i].num_neighbors++;
        if (p[i].num_neighbors > max_neighbors) {
          printf("Found too many neighbors: %d > %d\n", p[i].num_neighbors, max_neighbors);
          return -1;
        }
        p[i].neighbors[index] = j;
      }
    }
    most_neighbors = max(most_neighbors, p[i].num_neighbors);
  }
  return most_neighbors;
}

void update_neighbors(ball &a, int n, const ball *bs, int N,
                      double neighbor_R, const double len[3], int walls, int max_neighbors){
  a.num_neighbors = 0;
  for (int i = 0; i < N; i++){
    if ((i != n) &&
        (periodic_diff(a.pos, bs[i].neighbor_center, len, walls).normsquared()
         < sqr(a.R + bs[i].R + neighbor_R))){
      a.neighbors[a.num_neighbors] = i;
      a.num_neighbors++;
      assert(a.num_neighbors < max_neighbors);
    }
  }
}

inline void add_neighbor(int new_n, ball *p, int id, int max_neighbors){
  int i = p[id].num_neighbors;
  while (i > 0 && p[id].neighbors[i-1] > new_n){
    p[id].neighbors[i] = p[id].neighbors[i-1];
    i --;
  }
  p[id].neighbors[i] = new_n;
  p[id].num_neighbors ++;
  assert(p[id].num_neighbors < max_neighbors);
}

inline void remove_neighbor(int old_n, ball *p, int id){
  int i = p[id].num_neighbors - 1;
  int temp = p[id].neighbors[i];
  while (temp != old_n){
    i --;
    const int temp2 = temp;
    temp = p[id].neighbors[i];
    p[id].neighbors[i] = temp2;
  }
  p[id].num_neighbors --;
}

void inform_neighbors(const ball &new_p, const ball &old_p, ball *p, int n, int max_neighbors){
  int new_index = 0, old_index = 0;
  while (true){
    if (new_index == new_p.num_neighbors){
      for(int i = old_index; i < old_p.num_neighbors; i++)
        remove_neighbor(n, p, old_p.neighbors[i]);
      return;
    }
    if (old_index == old_p.num_neighbors){
      for(int i = new_index; i < new_p.num_neighbors; i++) {
        add_neighbor(n, p, new_p.neighbors[i], max_neighbors);
      }
      return;
    }
    if (new_p.neighbors[new_index] < old_p.neighbors[old_index]){
      add_neighbor(n, p, new_p.neighbors[new_index], max_neighbors);
      new_index ++;
    } else if (old_p.neighbors[old_index] < new_p.neighbors[new_index]){
      remove_neighbor(n, p, old_p.neighbors[old_index]);
      old_index ++;
    } else {
      new_index ++;
      old_index ++;
    }
  }
}

bool overlap(const ball &a, const ball &b, const double len[3], int walls){
  const vector3d ab = periodic_diff(a.pos, b.pos, len, walls);
  return (ab.normsquared() < sqr(a.R + b.R));
}

int overlaps_with_any(const ball &a, const ball *p, const double len[3], int walls){
  for (int i = 0; i < a.num_neighbors; i++){
    if (overlap(a,p[a.neighbors[i]],len,walls))
      return true;
  }
  return false;
}

static const int wall_stickiness = 2;

int count_interactions(int id, ball *p, double interaction_distance,
                       double len[3], int walls, int sticky_wall){
  int interactions = 0;
  for(int i = 0; i < p[id].num_neighbors; i++){
    if(periodic_diff(p[id].pos, p[p[id].neighbors[i]].pos,
                     len, walls).normsquared()
       <= uipow(interaction_distance,2))
      interactions++;
  }
  // if sticky_wall is true, then there is an attractive slab right
  // near the -z wall.
  if (sticky_wall && p[id].pos.x < p[id].R) {
    interactions += wall_stickiness;
  }
  return interactions;
}

int count_all_interactions(ball *balls, int N, double interaction_distance,
                           double len[3], int walls, int sticky_wall) {
  // Count initial number of interactions
  // Sum over i < k for all |ball[i].pos - ball[k].pos| < interaction_distance
  int interactions = 0;
  for(int i = 0; i < N; i++) {
    for(int j = 0; j < balls[i].num_neighbors; j++) {
      if(i < balls[i].neighbors[j]
         && periodic_diff(balls[i].pos,
                          balls[balls[i].neighbors[j]].pos,
                          len, walls).norm()
         <= interaction_distance)
        interactions++;
    }
    // if sticky_wall is true, then there is an attractive slab right
    // near the -z wall.
    if (sticky_wall && balls[i].pos.x < balls[i].R) {
      interactions += wall_stickiness;
    }
  }
  return interactions;
}

vector3d fcc_pos(int n, int m, int l, double x, double y, double z, double a){
  return a*vector3d(n+x/2,m+y/2,l+z/2);
}

int max_balls_within(double distance){ // distances are in units of ball radius
  distance += 1e-10; // add a tiny, but necessary margin of error
  double a = 2*sqrt(2); // fcc lattice constant
  int c = int(ceil(distance/a)); // number of cubic fcc cells to go out from center
  int num = -1; // number of balls within a given radius; don't count the center ball

  int xs[] = {0,1,1,0};
  int ys[] = {0,1,0,1};
  int zs[] = {0,0,1,1};
  for(int n  = -c; n <= c; n++){
    for(int m = -c; m <= c; m++){
      for(int l = -c; l <= c; l++){
        for(int k = 0; k < 4; k++)
          num += (fcc_pos(n,m,l,xs[k],ys[k],zs[k],a).norm() <= distance);
      }
    }
  }
  return num;
}

// sw_simulation methods

void sw_simulation::reset_histograms(){

  moves.total = 0;
  moves.working = 0;

  for(int i = 0; i < energy_levels; i++){
    energy_histogram[i] = 0;
    optimistic_samples[i] = 0;
    pessimistic_samples[i] = 0;
    pessimistic_observation[i] = false;
  }
}

void sw_simulation::move_a_ball() {
  int id = moves.total % N;
  moves.total++;
  const int old_interaction_count =
    count_interactions(id, balls, interaction_distance, len, walls, sticky_wall);

  ball temp = balls[id];
  temp.pos = sw_fix_periodic(temp.pos + vector3d::ran(translation_scale), len);
  // If we overlap, this is a bad move! Because random_move always
  // calls sw_fix_periodic, we need not worry about moving out of the
  // cell.
  if (overlaps_with_any(temp, balls, len, walls)){
    transitions(energy, 0) += 1; // update the transition histogram
    end_move_updates();
    return;
  }
  const bool get_new_neighbors =
    (periodic_diff(temp.pos, temp.neighbor_center, len, walls).normsquared()
     > sqr(neighbor_R/2.0));
  if (get_new_neighbors){
    // If we've moved too far, then the overlap test may have given a false
    // negative. So we'll find our new neighbors, and check against them.
    // If we still don't overlap, then we'll have to update the tables
    // of our neighbors that have changed.
    temp.neighbors = new int[max_neighbors];
    update_neighbors(temp, id, balls, N, neighbor_R, len, walls, max_neighbors);
    moves.updates++;
    // However, for this check (and this check only), we don't need to
    // look at all of our neighbors, only our new ones.
    // fixme: do this!
    //int *new_neighbors = new int[max_neighbors];

    if (overlaps_with_any(temp, balls, len, walls)) {
      // turns out we overlap after all.  :(
      delete[] temp.neighbors;
      transitions(energy, 0) += 1; // update the transition histogram
      end_move_updates();
      return;
    }
  }
  // Now that we know that we are keeping the new move (unless the
  // weights say otherwise), and after we have updated the neighbor
  // tables if needed, we can compute the new interaction count.
  ball pid = balls[id]; // save a copy
  balls[id] = temp; // temporarily update the position
  const int new_interaction_count =
    count_interactions(id, balls, interaction_distance, len, walls, sticky_wall);
  balls[id] = pid;
  // Now we can check whether we actually want to do this move based on the
  // new energy.
  const int energy_change = new_interaction_count - old_interaction_count;
  transitions(energy, energy_change) += 1; // update the transition histogram
  double Pmove = 1;
  if ((use_wl||use_wltmmc)
      && (energy + energy_change > min_important_energy
          || energy+energy_change<max_entropy_state)) {
      // This means we are using a WL method, and the system is trying
      // to leave the energy range specified.  We cannot permit this!
      Pmove = 0;
  } else if (use_tmmc) {
    /* I note that Swendson 1999 uses essentially this method
       *after* two stages of initialization. */
    long tup_norm = 0;
    long tdown_norm = 0;
    for (int de=-biggest_energy_transition; de<=biggest_energy_transition; de++) {
      tup_norm += transitions(energy, de);
      tdown_norm += transitions(energy+energy_change, de);
    }
    const long ncounts_up = transitions(energy, energy_change);
    const long ncounts_down = transitions(energy+energy_change, -energy_change);
    const double tup = ncounts_up/double(tup_norm);
    const double tdown = ncounts_down/double(tdown_norm);
    // If the TMMC data looks remotely plausible, set Pmove appropriately.
    if (tup > 0 && tdown > 0) Pmove = tdown/tup;
  } else if (use_sad) {
    const int e1 = energy;
    const int e2 = energy + energy_change;
    double lnw1 = ln_energy_weights[e1];
    if (e1 < too_high_energy) {
      lnw1 = ln_energy_weights[too_high_energy];
    } else if (e1 > too_low_energy) {
      lnw1 = ln_energy_weights[too_low_energy] + (e1 - too_low_energy)/min_T;
    }
    double lnw2 = ln_energy_weights[e2];
    if (e2 < too_high_energy) {
      lnw2 = ln_energy_weights[too_high_energy];
    } else if (e2 > too_low_energy) {
      lnw2 = ln_energy_weights[too_low_energy] + (e2 - too_low_energy)/min_T;
    }
    const double lnPmove = lnw2 - lnw1;
    Pmove = exp(lnPmove);
    //if (e2 < too_high_energy && e1 != e2) {
      //printf("prob hi %d -> %d = %g\n", e1, e2, Pmove);
    //} else if (e2 > too_low_energy && e1 != e2) {
      //printf("prob lo %d -> %d = %g\n", e1, e2, Pmove);
    //}
  } else {
    const double lnPmove =
      ln_energy_weights[energy + energy_change] - ln_energy_weights[energy];
    if (lnPmove < 0) Pmove = exp(lnPmove);
  }
  if (Pmove < 1) {
    if (random::ran() > Pmove) {
      // We want to reject this move because it is too improbable
      // based on our weights.
      if (get_new_neighbors) delete[] temp.neighbors;
      end_move_updates();
      return;
    }
  }
  if (get_new_neighbors) {
    // Okay, we've checked twice, just like Santa Clause, so we're definitely
    // keeping this move and need to tell our neighbors where we are now.
    temp.neighbor_center = temp.pos;
    inform_neighbors(temp, balls[id], balls, id, max_neighbors);
    moves.informs++;
    delete[] balls[id].neighbors;
  }
  balls[id] = temp; // Yay, we have a successful move!
  moves.working++;
  energy += energy_change;

  if(energy_change != 0) energy_change_updates(energy_change);

  end_move_updates();
}

void sw_simulation::end_move_updates(){
   // update iteration counter, energy histogram, and walker counters
  if (moves.total % N == 0) iteration++;
  if (sa_t0) {
    wl_factor = sa_prefactor*sa_t0/max(sa_t0, moves.total);
  }
  energy_histogram[energy]++;
  if (use_sad) {
    if (energy_histogram[energy] == 1) {
      // This is the first time we ever got here!
      if (too_low_energy < 0 || too_high_energy < 0) {
        // This is our first ever move!
        too_low_energy = energy;
        too_high_energy = energy;
        num_sad_states = 1;
      }
      if (energy < too_low_energy && energy > too_high_energy) {
        num_sad_states++; // We just discovered a new interesting state!
        time_L = moves.total;
      }
    }
    if (energy_histogram[energy] > highest_hist) {
      highest_hist = energy_histogram[energy];
      if (energy < too_high_energy) {
        //printf("In High!\n");
        for (int i = energy; i < too_high_energy; i++) {
          if (energy_histogram[i]) {
              ln_energy_weights[i] = ln_energy_weights[too_high_energy]
                - log(energy_histogram[i]/double(highest_hist));
          } else {
            ln_energy_weights[i] = 0;
          }
        }
        num_sad_states = 0;
        // We need to update the number of states between the too high
        // and too low energies.
        for (int i=too_high_energy; i<=too_low_energy; i++) {
          if (energy_histogram[i]) num_sad_states++;
        }
        time_L = moves.total;
        too_high_energy = energy;
      } else if (energy > too_low_energy) {
        //printf("In low!\n");
        for (int i = too_low_energy; i <= energy; i++) {
          if (energy_histogram[i]) {
            ln_energy_weights[i] = ln_energy_weights[too_low_energy]
                - log(energy_histogram[i]/double(highest_hist))
                + (energy-too_low_energy)/min_T;
          } else {
            ln_energy_weights[i] = 0;
          }
        }
        // We need to update the number of states between the too high
        // and too low energies.
        num_sad_states = 0;
        for (int i=too_high_energy; i<=too_low_energy; i++) {
          if (energy_histogram[i]) num_sad_states++;
        }
        time_L = moves.total;
        too_low_energy = energy;
      }
    }
    if (moves.total == time_L) {
      printf("  (moves %ld, num_sad_states %d, erange: %d -> %d gamma = %g, oldgamma = %g)\n",
         moves.total, num_sad_states, too_low_energy, too_high_energy, wl_factor,
         sa_prefactor*num_sad_states*(too_low_energy-too_high_energy)
         /(min_T*use_sad*moves.total));
    }
    if (energy >= too_high_energy && energy <= too_low_energy) {
      //printf("In Interesting!\n");
      // We are in the "interesting" region, so use an ordinary SA update.
      if (too_low_energy > too_high_energy) {
        const double t = moves.total;
        const double dE = too_low_energy-too_high_energy;
    
        wl_factor = dE/(min_T*t*use_sad)
          *(num_sad_states*num_sad_states + num_sad_states*t + t*(t/time_L - 1))
          /(num_sad_states*num_sad_states + t + t*(t/time_L - 1));
    
        /*
          printf("       gamma = %g, oldgamma = %g   ratio %f num_sad_states %d\n",
                 wl_factor,
                 num_sad_states*(too_low_energy-too_high_energy)
                              /(min_T*use_sad*moves.total),
                 (num_sad_states*num_sad_states + num_sad_states*t + 0*t*(t/time_L - 1))
                 /(num_sad_states*num_sad_states + t + 0*t*(t/time_L - 1)),
                 num_sad_states);
        */
        ln_energy_weights[energy] -= wl_factor;
      }
    }
  } else {
    // Note: if not using WL or SA method, wl_factor = 0 and the
    // following has no effect.
    ln_energy_weights[energy] -= wl_factor;
  }
}

void sw_simulation::energy_change_updates(int energy_change){
  // If we're at or above the state of max entropy, we have not yet observed any energies
  if(energy <= max_entropy_state){
    for(int i = max_entropy_state; i < energy_levels; i++)
      pessimistic_observation[i] = false;
  } else if (!pessimistic_observation[energy]) {
    // If we have not yet observed this energy, now we have!
    pessimistic_observation[energy] = true;
    pessimistic_samples[energy]++;
  }

  if (energy_change > 0) optimistic_samples[energy]++;
}

void sw_simulation::flush_weight_array(){
  const double max_entropy_weight = ln_energy_weights[max_entropy_state];
  for (int i = 0; i < energy_levels; i++)
    ln_energy_weights[i] -= max_entropy_weight;
  // floor weights above state of max entropy
  for (int i = 0; i < max_entropy_state; i++)
    ln_energy_weights[i] = 0;
}

double* sw_simulation::compute_ln_dos(dos_types dos_type) {

  double *ln_dos = new double[energy_levels]();

  if(dos_type == histogram_dos){
    for(int i = max_entropy_state; i < energy_levels; i++){
      if(energy_histogram[i] != 0){
        ln_dos[i] = log(energy_histogram[i]) - ln_energy_weights[i];
      }
      else ln_dos[i] = -DBL_MAX;
    }
  } else if (dos_type == weights_dos) {
    // weights_dos is useful for WL, SAD, or SAMC algorithms, where
    // the density of states is determined directly from the weights.
    int minE = 0;
    double betamax = 1.0/min_T;
    if (use_sad) {
      // This is hokey, but we just want to ensure that we have a proper
      // max_entropy_state before computing the ln_dos.
      max_entropy_state = 0;
      for (int i=0; i<energy_levels; i++) {
        if (ln_energy_weights[i] < ln_energy_weights[max_entropy_state]) {
          max_entropy_state = i;
        }
      }
    }
    for (int i=0; i<energy_levels; i++) {
      ln_dos[i] = ln_energy_weights[max_entropy_state] - ln_energy_weights[i];
      if (!minE && ln_dos[i-1] - ln_dos[i] > betamax) minE = i;
    }
    if (use_sad) {
      // Above the max_entropy_state our weights are effectively constant,
      // so the density of states is proportional to our histogram.
      for (int i=0; i<too_high_energy; i++) {
        if (energy_histogram[i]) {
          ln_dos[i] = ln_dos[too_high_energy]
             + log(energy_histogram[i]/double(highest_hist));
        }
      }
      // Below the minimum important energy, we also need to use the histogram,
      // only now adjusted by a Boltzmann factor.  We compute the min
      // important energy above for extreme clarity.
      for (int i=too_low_energy+1; i<energy_levels; i++) {
        if (energy_histogram[i]) {
          ln_dos[i] = ln_dos[too_low_energy]
              + log(energy_histogram[i]/double(highest_hist))
            - (i-too_low_energy)*betamax;  // the last bit gives Boltzmann factor
        }
      }
      // Now let us set the ln_dos for any sites we have never visited
      // to be equal to the minimum value of ln_dos for sites we
      // *have* visited.  These are unknown densities of states, and
      // there is no particular reason to set them to be crazy low.
      double lowest_ln_dos = 0;
      for (int i=0; i<energy_levels; i++) {
        if (energy_histogram[i]) lowest_ln_dos = min(lowest_ln_dos, ln_dos[i]);
      }
      for (int i=0; i<energy_levels; i++) {
        if (!energy_histogram[i]) ln_dos[i] = lowest_ln_dos;
      }
    }
  } else if(dos_type == transition_dos) {
    ln_dos[0] = 0;
    for (int i=1; i<energy_levels; i++) {
      ln_dos[i] = ln_dos[i-1];
      double down_to_here = 0;
      double up_from_here = 0;
      for (int j=max(0,i-biggest_energy_transition); j<i; j++) {
        const double tdown = transition_matrix(i, j);
        if (tdown) {
          // we are careful here not to take the exponential (which
          // could give a NaN) unless we already know there is some
          // probability of making this transition.
          down_to_here += exp(ln_dos[j] - ln_dos[i])*tdown;
        }
        up_from_here += transition_matrix(j, i);
      }
      if (down_to_here > 0 && up_from_here > 0) {
        ln_dos[i] += log(down_to_here/up_from_here);
      }
    }
  } else {
    printf("We don't know what dos type we have!\n");
    exit(1);
  }
  return ln_dos;
}

int sw_simulation::set_min_important_energy(double *input_ln_dos){
  // We always use the transition matrix to estimate the
  // min_important_energy, since it is more robust at the outset.
  double *ln_dos;
  if (input_ln_dos) ln_dos = input_ln_dos;
  else ln_dos = compute_ln_dos(transition_dos);

  min_important_energy = 0;
  // Look for a energy which maximizes the free energy at temperature min_T
  for (int i=0; i < energy_levels; i++) {
    if (energy_histogram[i] &&
        ln_dos[i] + i/min_T > ln_dos[min_important_energy] + min_important_energy/min_T) {
      min_important_energy = i;
    }
    if (energy_histogram[i] && !energy_histogram[min_important_energy]) {
      min_important_energy = i;
    }
  }

  if (!input_ln_dos) delete[] ln_dos;

  return min_important_energy;
}

void sw_simulation::set_max_entropy_energy() {
  const double *ln_dos = compute_ln_dos(transition_dos);

  for (int i=energy_levels-1; i >= 0; i--) {
    if (ln_dos[i] > ln_dos[max_entropy_state]) max_entropy_state = i;
  }
  delete[] ln_dos;
}

static void print_seconds_as_time(clock_t clocks) {
  const double secs_done = double(clocks)/CLOCKS_PER_SEC;
  const int seconds = long(secs_done) % 60;
  const int minutes = long(secs_done / 60) % 60;
  const int hours = long(secs_done / 3600) % 24;
  const int days = long(secs_done / 86400);
  if (days == 0) {
    printf(" %02i:%02i:%02i ", hours, minutes, seconds);
  } else {
    printf(" %i days, %02i:%02i:%02i ", days, hours, minutes, seconds);
  }
}

double sw_simulation::converged_to_temperature(double *ln_dos) const {
  int e = converged_to_state();
  return 1.0/(ln_dos[e-1] - ln_dos[e]);
}

int sw_simulation::converged_to_state() const {
  for (int i = max_entropy_state+1; i < energy_levels; i++) {
    if (pessimistic_samples[i] < 10) {
      if (i == 1) {
        // This is a special case for when we have only ever seen one
        // energy.  This energy will be min_important_energy, and we
        // need to include that energy in the output dos.
        return min_important_energy;
      }
      return i-1;
    }
  }
  return min_important_energy;
}

bool sw_simulation::finished_initializing(bool be_verbose) {
  const clock_t now = clock();
  if (max_time > 0 && now/CLOCKS_PER_SEC > start_time + max_time) {
      printf("Ran out of time after %g seconds!\n", max_time);
      return true;
  }

  if(end_condition == optimistic_min_samples
            || end_condition == pessimistic_min_samples) {
    if(end_condition == optimistic_min_samples){
      if (be_verbose) {
        long num_to_go = 0, energies_unconverged = 0;
        int lowest_problem_energy = 0, highest_problem_energy = energy_levels-1;
        for (int i = min_important_energy; i > max_entropy_state; i--){
          if (optimistic_samples[i] < min_samples) {
            num_to_go += min_samples - optimistic_samples[i];
            energies_unconverged += 1;
            if (i > lowest_problem_energy) lowest_problem_energy = i;
            if (i < highest_problem_energy) highest_problem_energy = i;
          }
        }
        printf("[%9ld] Have %ld samples to go (at %ld energies)\n",
               iteration, num_to_go, energies_unconverged);
        printf("       <%d - %d> has samples <%ld(%ld) - %ld(%ld)>/%d (current energy %d",
               lowest_problem_energy, highest_problem_energy,
               optimistic_samples[lowest_problem_energy],
               pessimistic_samples[lowest_problem_energy],
               optimistic_samples[highest_problem_energy],
               pessimistic_samples[highest_problem_energy], min_samples, energy);
        printf(")\n");
        fflush(stdout);
      }
      for(int i = min_important_energy; i > max_entropy_state; i--){
        if (optimistic_samples[i] < min_samples) {
          return false;
        }
      }
      return true;
    } else { // if end_condition == pessimistic_min_samples
      if (be_verbose) {
        set_max_entropy_energy();
        set_min_important_energy();
        long energies_unconverged = 0;
        int highest_problem_energy = energy_levels-1;
        for (int i = min_important_energy; i > max_entropy_state; i--){
          if (pessimistic_samples[i] < min_samples) {
            energies_unconverged += 1;
            if (i < highest_problem_energy) highest_problem_energy = i;
          }
        }
        double *ln_dos = compute_ln_dos(transition_dos);
        const double nice_T = 1.0/(ln_dos[highest_problem_energy] - ln_dos[highest_problem_energy+1]);
        printf("[%9ld] Have %ld energies to go (down to T=%g or %g)\n",
               iteration, energies_unconverged, nice_T, converged_to_temperature(ln_dos));
        printf("       <%d - %d vs %d> has samples <%ld - %ld>/%d (current energy %d",
               min_important_energy, highest_problem_energy, max_entropy_state,
               pessimistic_samples[min_important_energy],
               pessimistic_samples[highest_problem_energy], min_samples, energy);
        delete[] ln_dos;
        if (use_sad) printf(", %.2g, t0 %.2g", wl_factor, wl_factor*moves.total);
        printf(")\n");
        {
          printf("      ");
          print_seconds_as_time(now);
          long pess = pessimistic_samples[min_important_energy];
          long percent_done = 100*pess/min_samples;
          printf("(%ld%% done", percent_done);
          if (pess > 0) {
            const clock_t clocks_remaining = now*(min_samples-pess)/pess;
            print_seconds_as_time(clocks_remaining);
            printf("remaining)\n");
          } else {
            printf(")\n");
          }
        }
        fflush(stdout);
      }
      return pessimistic_samples[min_important_energy] >= min_samples;
    }
  }

  else if(end_condition == flat_histogram){
    int hist_min = int(1e20);
    int hist_total = 0;
    int most_weighted_energy = 0;
    for(int i = max_entropy_state; i < energy_levels; i++){
      hist_total += energy_histogram[i];
      if(energy_histogram[i] < hist_min) hist_min = energy_histogram[i];
      if(ln_energy_weights[i] > ln_energy_weights[most_weighted_energy])
        most_weighted_energy = i;
    }
    const double hist_mean = hist_total/(min_important_energy-max_entropy_state);
    /* First, make sure that the histogram is sufficiently flat. In addition,
       make sure we didn't just get stuck at the most heavily weighted energy. */
    return hist_min >= flatness*hist_mean && energy != most_weighted_energy;
  }

  else if(end_condition == init_iter_limit) {
    if (be_verbose) {
      static int last_percent = 0;
      int percent = (100*iteration)/init_iters;
      if (percent > last_percent) {
        printf("%2d%% done (%ld/%ld iterations)\n",
               percent, long(iteration), long(init_iters));
        last_percent = percent;

        /* The following is a hokey and quick way to guess at a
           min_important_energy, which assumes a method such as tmmc,
           which puts a bound on the "effective temperature" at
           min_T. */
        int min_maybe_important_energy = energy_levels-1;
        for (int i=energy_levels-1; i>max_entropy_state;i--) {
          if (pessimistic_samples[i] && pessimistic_samples[i-1] &&
              energy_histogram[i]/double(energy_histogram[i-1]) > exp(-1.0/min_T)) {
            min_maybe_important_energy = i-1;
            break;
          }
        }
        int lowest_problem_energy = 0, highest_problem_energy = energy_levels-1;
        for (int i = min_maybe_important_energy; i > max_entropy_state; i--){
          if (pessimistic_samples[i] < 5 && energy_histogram[i]) {
            if (i > lowest_problem_energy) lowest_problem_energy = i;
            if (i < highest_problem_energy) highest_problem_energy = i;
          } else if (pessimistic_samples[i] > 5) {
            break;
          }
        }
        printf("       energies <%g to %g> have samples <%ld(%ld) to %ld(%ld)> (current energy %g)\n",
               -lowest_problem_energy/double(N), -highest_problem_energy/double(N),
               optimistic_samples[lowest_problem_energy],
               pessimistic_samples[lowest_problem_energy],
               optimistic_samples[highest_problem_energy],
               pessimistic_samples[highest_problem_energy], -energy/double(N));
        fflush(stdout);
      }
    }
    return iteration >= init_iters;
  } else if (max_time > 0) {
    return false;
  }

  printf("We are asking whether we are finished initializing without "
         "a valid end condition!\n");
  exit(1);
}

bool sw_simulation::reached_iteration_cap(){
  return end_condition == init_iter_limit && iteration >= init_iters;
}

// initialize the weight array using the specified temperature.
void sw_simulation::initialize_canonical(double T, int reference) {
  for(int i=reference+1; i < energy_levels; i++){
    ln_energy_weights[i] = ln_energy_weights[reference] + (i-reference)/T;
  }
}

// this method is under construction by DR and JP (2017).
// initialize the weight array using the wltmmc method.
void sw_simulation::initialize_wltmmc(double wl_fmod,
                                      double wl_threshold, double wl_cutoff) {
  int check_how_often =  N; // update WL stuff only so often
  assert(use_wltmmc);
  bool verbose = false;
  do {
    for (int i = 0; i < check_how_often && !reached_iteration_cap(); i++) move_a_ball();
    check_how_often += N; // try a little harder next time...

    verbose = printing_allowed();
    if (verbose) write_transitions_file();
    calculate_weights_using_wltmmc(wl_fmod, wl_threshold, wl_cutoff, verbose);
  } while(!finished_initializing(verbose));
}

// this is the end of code on WL-TMMC.

// initialize the weight array using the Wang-Landau method.
void sw_simulation::initialize_wang_landau(double wl_fmod,
                                           double wl_threshold, double wl_cutoff,
                                           bool fixed_energy_range) {
  assert(wl_factor);
  assert(use_wl);
  const double original_wl_factor = wl_factor;
  int weight_updates = 0;
  bool done = false;
  assert(min_important_energy);
  int old_min_important_energy = min_important_energy;
  while (!done) {

    for (int i=0; i < N*energy_levels && !reached_iteration_cap(); i++) {
      move_a_ball();
    }

    if(!fixed_energy_range){
      // Find and set the minimum important energy, as well as canonical weights below it
      set_min_important_energy();
      set_max_entropy_energy();
      initialize_canonical(min_T,min_important_energy);
      if (min_important_energy > old_min_important_energy && wl_factor != original_wl_factor) {
        printf("\nFound new energy states!\n");
        printf("  min_important_energy goes from %d -> %d\n",
               old_min_important_energy, min_important_energy);
        printf("  wl_factor goes from %g -> %g\n",
               wl_factor, original_wl_factor);
        wl_factor = original_wl_factor;
        old_min_important_energy = min_important_energy;
        flush_weight_array();
        for (int i = 0; i < energy_levels; i++) {
          if (energy_histogram[i] > 0) energy_histogram[i] = 1;
        }
        continue; // don't even considering quitting when we just
                  // discovered a new energy!
      }
    }

    // compute variation in energy histogram
    int highest_hist_i = 0; // the most commonly visited energy
    int lowest_hist_i = 0; // the least commonly visited energy
    double highest_hist = 0; // highest histogram value
    double lowest_hist = 1e200; // lowest histogram value
    double total_counts = 0; // total counts in energy histogram
    int num_nonzero = 0; // number of nonzero bins
    for (int i = max_entropy_state; i <= min_important_energy; i++) {
      num_nonzero += 1;
      total_counts += energy_histogram[i];
      if(energy_histogram[i] > highest_hist){
        highest_hist = energy_histogram[i];
        highest_hist_i = i;
      }
      if(energy_histogram[i] < lowest_hist){
        lowest_hist = energy_histogram[i];
        lowest_hist_i = i;
      }
    }
    double hist_mean = (double)total_counts / (min_important_energy - max_entropy_state);
    const double variation = hist_mean/lowest_hist - 1;
    const double min_over_mean = lowest_hist/hist_mean;
    const long min_interesting_energy_count = energy_histogram[min_important_energy];

    // print status text for testing purposes
    bool be_verbose = printing_allowed();

    // check whether our histogram is flat enough to update wl_factor
    if (min_over_mean >= wl_threshold) {
      weight_updates += 1;
      be_verbose = true;
      wl_factor /= wl_fmod;
      printf("We reached WL flatness (%ld moves, wl_factor %g)!\n",
             moves.total, wl_factor);
      flush_weight_array();
      for (int i = 0; i < energy_levels; i++) {
        if (energy_histogram[i] > 0) energy_histogram[i] = 1;
      }

      // repeat until terminal condition is met
      if (wl_factor < wl_cutoff && end_condition != init_iter_limit) {
        printf("Took %ld iterations and %i updates to initialize with Wang-Landau method.\n",
               iteration, weight_updates);
        done = true;
      }
    }
    if (be_verbose) {
      write_transitions_file(); // Just for the heck of it, save the transition matrix...
      printf("WL weight update: %i\n",weight_updates);
      printf("  WL factor: %g\n",wl_factor);
      printf("  count variation: %g (min/mean %g)\n", variation, min_over_mean);
      printf("  highest/lowest histogram energies (values): %d (%.2g) / %d (%.2g)\n",
             highest_hist_i, highest_hist, lowest_hist_i, lowest_hist);
      printf("  round trips at min E: %ld (max S - 1): %ld (counts at minE: %ld)\n\n",
             pessimistic_samples[min_important_energy], pessimistic_samples[max_entropy_state+1],
             min_interesting_energy_count);
    }
  }

  initialize_canonical(min_T,min_important_energy);
}

// stochastic_weights is under construction by DR and JP (2017).
// this is used for Stochastic Approximation Monte Carlo.

void sw_simulation::initialize_samc(int am_sad) {
  use_sad = am_sad;
  assert(sa_t0 || am_sad);
  assert(sa_prefactor);

  int check_how_often =  N*N; // check if finished only so often
  bool verbose = false;
  do {
    for (int i = 0; i < check_how_often && !reached_iteration_cap(); i++) move_a_ball();
    check_how_often += N*N; // try a little harder next time...

    verbose = printing_allowed();
    if (verbose) {
      set_min_important_energy();
      set_max_entropy_energy();
      write_transitions_file();
    }
  } while(!finished_initializing(verbose));

  initialize_canonical(min_T,min_important_energy);
}

/* This method implements the optimized ensemble using the transition
   matrix information.  This should give a similar set of weights to
   the optimized_ensemble approach. */
void sw_simulation::optimize_weights_using_transitions(int version) {
  // Assume that we already *have* a reasonable set of weights (with
  // which to compute the diffusivity), and that we have already
  // defined the min_important_energy.
  update_weights_using_transitions(version);
  const double *ln_dos = compute_ln_dos(transition_dos);

  double diffusivity = 1;
  for(int i = max_entropy_state; i < energy_levels; i++) {
    double norm = 0, mean_sqr_de = 0, mean_de = 0;
    for (int de=-biggest_energy_transition;de<=biggest_energy_transition;de++) {
      // cap the ratio of weights at 1
      double T = transitions(i, de)*exp(max(0,ln_dos[biggest_energy_transition+i]
                                            -ln_dos[biggest_energy_transition+i+de]));
      norm += T;
      mean_sqr_de += T*double(de)*de;
      mean_de += T*double(de);
    }
    if (norm) {
      mean_sqr_de /= norm;
      mean_de /= norm;
      //printf("%4d: <de> = %15g   <de^2> = %15g\n", i, mean_de, mean_sqr_de);
      diffusivity = fabs(mean_sqr_de - mean_de*mean_de);
    }
    /* This is a different way of computing it than is done by Trebst,
       Huse and Troyer, but uses the formula that they derived at the
       end of Section IIA (and expressed in words).  The main
op       difference is that we compute the diffusivity here *directly*
       rather than inferring it from the walker gradient.  */
    ln_energy_weights[i] -= 0.5*log(diffusivity);
  }
  // Now we just define the maximum weight to be 1.
  for (int i=0; i<max_entropy_state; i++) {
    ln_energy_weights[i] = ln_energy_weights[max_entropy_state];
  }
  double ln_max = ln_energy_weights[max_entropy_state];
  for (int i=0;i<max_entropy_state;i++) {
    ln_energy_weights[i] = 0;
  }
  for (int i=max_entropy_state;i<energy_levels;i++) {
    ln_energy_weights[i] -= ln_max;
  }
  delete[] ln_dos;
}

// update the weight array using transitions
void sw_simulation::update_weights_using_transitions(int version, bool energy_range_fixed) {
  double *ln_dos = compute_ln_dos(transition_dos);
  if (!energy_range_fixed) {
    set_min_important_energy(ln_dos);
    // Let us be cautious and just ensure that we always have the proper
    // max_entropy_state.  This is probably redundant, but especially
    // when version>1 an error in max_entropy_state could cause real
    // trouble.
    int old_max_entropy_state = max_entropy_state;
    for (int i=0; i<=energy_levels; i++) {
      if (ln_dos[i] > ln_dos[max_entropy_state]) {
        max_entropy_state = i;
      }
    }
    if (old_max_entropy_state > max_entropy_state+1) {
      // We should zero out our pessimistic_samples, since we apparently
      // didn't have a clear picture of what it meant to randomize the
      // system.  We allow for a change of 1 (the minimal change) so as
      // to avoid trashing data when going between two states with
      // almost equal (max) entropy.
      printf("I am resetting the histograms, because max_entropy_state changed.\n");
      fflush(stdout);
      fprintf(stderr, "I am resetting the histograms, because max_entropy_state changed.\n");
      for(int i = 0; i < energy_levels; i++){
        pessimistic_samples[i] = 0;
        pessimistic_observation[i] = false;
      }
    }
  }
  // Above the max_entropy_state we level out the weights.
  for (int i = 0; i <= max_entropy_state; i++) {
    ln_energy_weights[i] = -ln_dos[max_entropy_state];
  }
  if (version == 1) {
    // Down to the min_important_energy we use the DOS for the weights.
    for (int i = max_entropy_state; i < energy_levels; i++) {
      // The following is new code added to make the code more
      // intelligently conservative when it comes to believing the
      // density of states when there are poor statistics.
      if (pessimistic_samples[i] && ln_dos[i] < ln_dos[i-1]) {
        // the following is ln of 1/sqrt(ps), which is a fractional
        // uncertainty in our count at energy i.
        double ln_uncertainty = -0.5*log(pessimistic_samples[i]);
        double ln_dos_ratio = ln_dos[i] - ln_dos[i-1];
        ln_energy_weights[i] = ln_energy_weights[i-1] + min(-ln_dos_ratio,
                                                            -ln_uncertainty);
      } else {
        // This handles the case where we've never seen this energy
        // before.  Just set its weight equal to that of the next higher
        // energy.
        ln_energy_weights[i] = ln_energy_weights[i-1];
      }
    }
    // At lower energies, we use Boltzmann weights with the minimum
    // temperature we are interested in, except in cases where the
    // ln_dos is greater than the Boltzmann factor would predict.
    for (int i = min_important_energy+1; i < energy_levels; i++) {
      ln_energy_weights[i] = min(ln_energy_weights[i-1] + 1.0/min_T, ln_energy_weights[i]);
    }
  } else if (version == 2 || version == 3) {
    // The slope on the log graph is the thermodynamic quantity we
    // describe as beta, so that is what we call it here.  We choose
    // to define beta to be positive (as physical beta=1/kT values
    // would be), which requires some juggling of signs below, since
    // our energies are opposite.
    double beta = 0;
    int pivot = 0;
    for (int i = max_entropy_state+1; i <= energy_levels; i++) {
      // Here is a simpler approach.  We just use the ln_dos until it
      // becomes implausible, and then we extend linearly down with a
      // secant (or tangent for version 3) line in the log graph.
      if (!pivot) {
        if (ln_dos[i-1] - ln_dos[i] > 1/min_T) {
          // We have reached the minimum temperature we care about!  At
          // lower energies, we will use Boltzmann weights with the
          // minimum temperature we are interested in.
          beta = 1/min_T;
          pivot = i-1;
        } else if (ln_dos[i] < ln_dos[i-1]
                   && ln_dos[i-1]-ln_dos[i] < 0.5*log(pessimistic_samples[i]) ) {
          ln_energy_weights[i] = -ln_dos[i];
        } else {
          pivot = i-1;
          if (version == 2) {
            beta = (ln_dos[max_entropy_state] - ln_dos[pivot])/(pivot-max_entropy_state);
          } else {
            beta = ln_dos[i-2] - ln_dos[i-1]; // just set it to the tangent!
          }
          if (beta != beta) beta = 0;
          for (int j=pivot+1; j<=energy_levels && pessimistic_samples[j]; j++) {
            // avoid setting the beta to intersect with the DOS at
            // any energy where we have any information about the DOS.
            double beta_here = (ln_dos[pivot] - ln_dos[j])/(j-pivot);
            beta = min(beta, beta_here);
          }
          beta = max(beta, 0);  // never make lower energies *less* probable
        }
      }
      if (pivot) {
        ln_energy_weights[i] = ln_energy_weights[pivot] + beta*(i-pivot);
      }
    }
  } else {
    printf("BAD TMI VERSION %d!@!!\n", version);
    fprintf(stderr, "BAD TMI VERSION %d!@!!\n", version);
    fflush(stdout);
    exit(1);
  }
  delete[] ln_dos;
}

// calculate_weights is under construction by DR and JP (2017).

// calculate the weight array using transitions for wltmmc
void sw_simulation::calculate_weights_using_wltmmc(double wl_fmod,
                                                   double wl_threshold,
                                                   double wl_cutoff,
                                                   bool verbose) {
  assert(use_wltmmc);
  assert(min_important_energy);
  if (wl_factor < wl_cutoff) {
    if (wl_factor > 0.0) {
      printf("All done with WL portion of WLTMMC!\n");
    }
    wl_factor = 0.0; // We are done with WL portion!  :)
    use_tmmc = true; // Now we will be doing TMMC like anyone else!
    return;
  }

  // compute variation in energy histogram
  int highest_hist_i = 0; // the most commonly visited energy
  int lowest_hist_i = 0; // the least commonly visited energy
  double highest_hist = 0; // highest histogram value
  double lowest_hist = 1e200; // lowest histogram value
  double total_counts = 0; // total counts in energy histogram
  int num_nonzero = 0; // number of nonzero bins

  for(int i = max_entropy_state+1; i <= min_important_energy; i++){
    num_nonzero += 1;
    total_counts += energy_histogram[i];
    if(energy_histogram[i] > highest_hist){
      highest_hist = energy_histogram[i];
      highest_hist_i = i;
    }
    if(energy_histogram[i] < lowest_hist){
      lowest_hist = energy_histogram[i];
      lowest_hist_i = i;
    }
  }
  double hist_mean = (double)total_counts / (min_important_energy - max_entropy_state);
  if (lowest_hist == 0) {
    if (verbose) {
      printf("We have never yet visited %d!\n", lowest_hist_i);
    }
  } else {
    const double min_over_mean = lowest_hist/hist_mean;
    const long min_interesting_energy_count = energy_histogram[min_important_energy];

    bool we_changed = false;
    // check whether our histogram is flat enough to update wl_factor.
    // We are choosing to have wl_threshold=1 mean that as long as
    // everything has been visited once we are permitted to move on.
    if (min_over_mean >= wl_threshold || wl_threshold == 1) {
      we_changed = true;
      wl_factor /= wl_fmod;
      printf("We reached WL flatness (%ld moves, wl_factor %g)!\n",
             moves.total, wl_factor);
      for (int i = 0; i < energy_levels; i++) {
        energy_histogram[i] = 0;
      }

      // We throw away the weight array that we just accumulated,
      // and replace it with one computed using the transition
      // matrix we have so far accumulated.

      // This is referred to by Shell 2003 as "refreshing" the density
      // of states periodically.  They do not specify precisely when
      // to "refresh", but we are doing so each time the WL approach
      // says to decrease the wl_factor.
      update_weights_using_transitions(1, true);
    }
    if (verbose || we_changed) {
      printf("  WL factor: %g (vs %g)\n",wl_factor, wl_cutoff);
      printf("  min/mean %g\n", min_over_mean);
      printf("  highest/lowest histogram energies (values): %d (%.2g) / %d (%.2g)\n",
             highest_hist_i, highest_hist, lowest_hist_i, lowest_hist);
      printf("  round trips at min E: %ld (max S - 1): %ld (counts at minE: %ld)\n\n",
             pessimistic_samples[min_important_energy], pessimistic_samples[max_entropy_state+1],
             min_interesting_energy_count);
    }
  }
} // done with WL!

// initialization with tmi
void sw_simulation::initialize_tmi(int version) {
  int check_how_often = N*N; // avoid wasting time if we are done
  bool verbose = false;
  do {
    for (int i = 0; i < check_how_often && !reached_iteration_cap(); i++) move_a_ball();
    check_how_often += N*N; // try a little harder next time...
    verbose = printing_allowed();
    if (verbose) {
      set_min_important_energy();
      write_transitions_file();
    }

    set_min_important_energy();
    update_weights_using_transitions(version);
  } while(!finished_initializing(verbose));
}

// initialization with toe
void sw_simulation::initialize_toe(int version) {
  int check_how_often = N*N; // avoid wasting time if we are done
  bool verbose = false;
  do {
    for (int i = 0; i < check_how_often && !reached_iteration_cap(); i++) move_a_ball();
    check_how_often += N*N; // try a little harder next time...
    verbose = printing_allowed();
    if (verbose) {
      set_min_important_energy();
      write_transitions_file();
    }

    set_min_important_energy();
    optimize_weights_using_transitions(version);
  } while(!finished_initializing(verbose));
}

// initialization with tmmc
void sw_simulation::initialize_transitions() {
  assert(use_tmmc);
  int check_how_often = N*N; // avoid wasting time if we are done
  bool verbose = false;
  do {
    for (int i = 0; i < check_how_often && !reached_iteration_cap(); i++) move_a_ball();
    check_how_often += N*N; // try a little harder next time...
    verbose = printing_allowed();
    if (verbose) {
      set_min_important_energy();
      set_max_entropy_energy();
      write_transitions_file();
    }
  } while(!finished_initializing(verbose));

  update_weights_using_transitions(1);
  set_min_important_energy();
}

static void write_t_file(sw_simulation &sw, const char *fname) {
  FILE *f = fopen(fname,"w");
  if (!f) {
    printf("Unable to create file %s!\n", fname);
    exit(1);
  }
  int greatest_dE = 0;
  int least_dE = 0;
  for (int i = 0; i < sw.energy_levels; i++) {
    for (int de = -sw.biggest_energy_transition; de <= sw.biggest_energy_transition; de++) {
      if (sw.transitions(i,de)) {
        if (de < least_dE) least_dE = de;
        if (de > greatest_dE) greatest_dE = de;
      }
    }
  }
  sw.write_header(f);
  fprintf(f, "#       \tde\n");
  fprintf(f, "# energy");
  for (int de = least_dE; de <= greatest_dE; de++) {
    fprintf(f, "\t%d", de);
  }
  fprintf(f, "\n");
  for(int i = 0; i < sw.energy_levels; i++) {
    bool have_i = false;
    for (int de = least_dE; de <= greatest_dE; de++) {
      if (sw.transitions(i,de)) have_i = true;
    }
    if (have_i){
      fprintf(f, "%d", i);
      for (int de = least_dE; de <= greatest_dE; de++) {
        fprintf(f, "\t%ld", sw.transitions(i, de));
      }
      fprintf(f, "\n");
    }
  }
  fclose(f);
}

static void write_d_file(sw_simulation &sw, const char *fname) {
  FILE *f = fopen(fname,"w");
  if (!f) {
    printf("Unable to create file %s!\n", fname);
    exit(1);
  }
  sw.write_header(f);
  dos_types how_to_compute_dos = transition_dos;
  if (sw.use_sad || sw.sa_t0 || sw.use_wl) how_to_compute_dos = weights_dos;
  double *lndos = sw.compute_ln_dos(how_to_compute_dos);
  double *lndos_transitions = sw.compute_ln_dos(transition_dos);
  double maxdos = lndos[0];
  double maxdos_transitions = lndos_transitions[0];
  if (how_to_compute_dos != transition_dos) {
    fprintf(f, "# energy\tlndos\tps\tlndos_tm\n");
  } else {
    fprintf(f, "# energy\tlndos\tps\n");
  }
  for (int i = 0; i < sw.energy_levels; i++) {
    if (maxdos < lndos[i]) maxdos = lndos[i];
    if (maxdos_transitions < lndos_transitions[i]) maxdos_transitions = lndos_transitions[i];
  }
  for (int i = 0; i < sw.energy_levels; i++) {
    if (how_to_compute_dos != transition_dos) {
      fprintf(f, "%d\t%g\t%ld\t%g\n", i, lndos[i] - maxdos, sw.pessimistic_samples[i],
              lndos_transitions[i] - maxdos_transitions);
    } else {
      fprintf(f, "%d\t%g\t%ld\n", i, lndos[i] - maxdos, sw.pessimistic_samples[i]);
    }
  }
  fclose(f);
  delete[] lndos;
  delete[] lndos_transitions;
}

static void write_lnw_file(sw_simulation &sw, const char *fname) {
  FILE *f = fopen(fname,"w");
  if (!f) {
    printf("Unable to create file %s!\n", fname);
    exit(1);
  }
  sw.write_header(f);
  fprintf(f, "# energy\tlnw\n");
  double minw = sw.ln_energy_weights[0];
  for (int i = 0; i < sw.energy_levels; i++) {
    if (minw > sw.ln_energy_weights[i]) minw = sw.ln_energy_weights[i];
  }
  for (int i = 0; i < sw.energy_levels; i++) {
    fprintf(f, "%d\t%g\n", i, sw.ln_energy_weights[i] - minw);
  }
  fclose(f);
}

void sw_simulation::write_transitions_file() {
  // silently do not save if there is not file name
  if (transitions_filename) write_t_file(*this, transitions_filename);

  if (transitions_movie_filename_format) {
    char *fname = new char[4096];
    struct stat st;
    do {
      // This loop increments transitions_movie_count until it reaches
      // an unused file name.  The idea is to enable two or more
      // simulations to contribute together to a single movie.
      sprintf(fname, transitions_movie_filename_format, transitions_movie_count++);
    } while (!stat(fname, &st));
    write_t_file(*this, fname);
    delete[] fname;
  }
  if (dos_movie_filename_format) {
    char *fname = new char[4096];
    struct stat st;
    do {
      // This loop increments dos_movie_count until it reaches
      // an unused file name.  The idea is to enable two or more
      // simulations to contribute together to a single movie.
      sprintf(fname, dos_movie_filename_format, dos_movie_count++);
    } while (!stat(fname, &st));
    write_d_file(*this, fname);
    delete[] fname;
  }
  if (lnw_movie_filename_format) {
    char *fname = new char[4096];
    struct stat st;
    do {
      // This loop increments lnw_movie_count until it reaches
      // an unused file name.  The idea is to enable two or more
      // simulations to contribute together to a single movie.
      sprintf(fname, lnw_movie_filename_format, lnw_movie_count++);
    } while (!stat(fname, &st));
    write_lnw_file(*this, fname);
    delete[] fname;
  }
}

void sw_simulation::write_header(FILE *f) {
  double *ln_dos = compute_ln_dos(transition_dos);

  fprintf(f, "# version: %s\n", version_identifier());
  fprintf(f, "# seed: %ld\n", random::seedval);
  fprintf(f, "# well_width: %g\n", well_width);
  fprintf(f, "# ff: %.16g\n", filling_fraction);
  fprintf(f, "# N: %d\n", N);
  fprintf(f, "# walls: %d\n", walls);
  fprintf(f, "# cell dimensions: (%g, %g, %g)\n", len[0], len[1], len[2]);
  fprintf(f, "# translation_scale: %g\n", translation_scale);
  fprintf(f, "# energy_levels: %d\n", energy_levels);
  fprintf(f, "# min_T: %g\n", min_T);
  fprintf(f, "# max_entropy_state: %d\n", max_entropy_state);
  fprintf(f, "# min_important_energy: %d\n", min_important_energy);
  fprintf(f, "# too_high_energy: %d\n", too_high_energy);
  fprintf(f, "# too_low_energy: %d\n", too_low_energy);

  fprintf(f, "\n");

  if (use_sad || sa_t0 || use_wl) {
    fprintf(f, "# WL Factor: %g\n", wl_factor);
  }

  fprintf(f, "# iterations: %ld\n", iteration);
  fprintf(f, "# working moves: %ld\n", moves.working);
  fprintf(f, "# total moves: %ld\n", moves.total);
  fprintf(f, "# acceptance rate: %g\n", double(moves.working)/moves.total);

  fprintf(f, "\n");

  fprintf(f, "# converged state: %d\n", converged_to_state());
  fprintf(f, "# converged temperature: %g\n", converged_to_temperature(ln_dos));
  delete[] ln_dos;
  fprintf(f, "\n");
}

// initialize by reading transition matrix from file
void sw_simulation::initialize_transitions_file(const char *transitions_input_filename){
  // open the transition matrix data file as read-only
  FILE *transitions_infile = fopen(transitions_input_filename,"r");

  // spit out an error and exist if the data file does not exist
  if(transitions_infile == NULL){
    printf("Cannot find transition matrix input file: %s\n",transitions_input_filename);
    exit(254);
  }

  const int line_len = 1000;
  char line[line_len];
  int min_de;

  // gather and verify metadata
  while(fgets(line,line_len,transitions_infile) != NULL){

    /* check that the metadata in the transition matrix file
       agrees with our simulation parameters */

    // check well width agreement
    if(strstr(line,"# well_width:") != NULL){
      double file_ww;
      if (sscanf(line,"%*s %*s %lf",&file_ww) != 1) {
        printf("Unable to read well-width properly from \"%s\"\n", line);
        exit(1);
      }
      if (file_ww != well_width) {
        printf("The well width in the transition matrix file metadata (%g) disagrees "
               "with that requested for this simulation (%g)!\n", file_ww, well_width);
        exit(232);
      }
    }

    // check filling fraction agreement
    if(strstr(line,"# ff:") != NULL){
      double file_ff;
      if (sscanf(line,"%*s %*s %lf", &file_ff) != 1) {
        printf("Unable to read ff properly from '%s'\n", line);
        exit(1);
      }
      if (fabs(file_ff - filling_fraction)/filling_fraction > 0.01/N) {
        printf("The filling fraction in the transition matrix file metadata (%g) disagrees "
               "with that requested for this simulation (%g)!\n", file_ff, filling_fraction);
        exit(233);
      }
    }

    // check N agreement
    if(strstr(line,"# N:") != NULL){
      int file_N;
      if (sscanf(line,"%*s %*s %i", &file_N) != 1) {
        printf("Unable to read N properly from '%s'\n", line);
        exit(1);
      }
      if(file_N != N){
        printf("The number of spheres in the transition matrix file metadata (%i) disagrees "
               "with that requested for this simulation (%i)!\n", file_N, N);
        exit(234);
      }
    }

    // check that we have a sufficiently small min_T in the data file
    if(strstr(line,"# min_T:") != NULL){
      double file_min_T;
      if (sscanf(line,"%*s %*s %lf", &file_min_T) != 1) {
        printf("Unable to read min_T properly from '%s'\n", line);
        exit(1);
      }
      if(file_min_T > min_T){
        printf("The minimum temperature in the transition matrix file metadata (%g) is "
               "larger than that requested for this simulation (%g)!\n", file_min_T, min_T);
      }
    }

    /* find the minimum de in the transition matrix as stored in the file.
       the line we match here should be the last commented line in the data file,
       so we break out of the metadata loop after storing min_de */
    if(strstr(line,"# energy\t") != NULL){
      if (sscanf(line,"%*s %*s %d", &min_de) != 1) {
        printf("Unable to read min_de properly from '%s'\n", line);
        exit(1);
      }
      break;
    }
  }

  // read in transition matrix
  /* when we hit EOF, we won't know until after trying to scan past it,
     so we loop while true and enforce a break condition */
  int e, min_e = 0;
  while(true){
    if (fscanf(transitions_infile,"%i",&e) != 1) {
      break;
    }
    if (!min_e) min_e = e;
    char nextc = 0; // keep going until we have reached the end of the line.
    for (int de=min_de; nextc != '\n'; de++) {
      if (fscanf(transitions_infile,"%li%c",&transitions(e,de), &nextc) != 2) {
        break;
      }
    }
  }

  // we are done with the data file
  fclose(transitions_infile);

  // initialize histogram from our saved transition data
  for (int i = 0; i < energy_levels; i++) {
    energy_histogram[i] = 0;
    for (int de=-biggest_energy_transition; de<=biggest_energy_transition; de++) {
      energy_histogram[i] += transitions(i,0);
    }
  }

  // now construct the actual weight array
  /* FIXME: it appears that we are reading in the data file properly,
     but for some reason we are still not getting proper weights */
  update_weights_using_transitions(1);
  flush_weight_array();
  set_min_important_energy();
  initialize_canonical(min_T,min_important_energy);
}

bool sw_simulation::printing_allowed(){
  const double max_time_skip = 60*30; // 1/2 hour
  const double initial_time_skip = 3; // seconds
  static double time_skip = initial_time_skip;
  static int every_so_often = 0;

  static clock_t last_output = clock(); // when we last output data

  if (++every_so_often > time_skip/estimated_time_per_iteration) {
    fflush(stdout); // flushing once a second will be no problem and can be helpful
    clock_t now = clock();
    time_skip = min(time_skip + initial_time_skip, max_time_skip);

    // update our setimated time per iteration based on actual time
    // spent in this round of iterations
    double elapsed_time = (now - last_output)/double(CLOCKS_PER_SEC);
    if (now > last_output) {
      estimated_time_per_iteration = elapsed_time / every_so_often;
    } else {
      estimated_time_per_iteration = 0.1 / every_so_often / double(CLOCKS_PER_SEC);
    }
    last_output = now;
    every_so_often = 0;
    return true;
  }
  return false;
}

