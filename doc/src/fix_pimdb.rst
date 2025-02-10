.. index:: fix pimdb/langevin
.. index:: fix pimdb/nvt

fix pimdb/langevin command
==========================

fix pimdb/nvt command
=====================

Syntax
""""""

.. code-block:: LAMMPS

   fix ID group-ID style keyword value ...

* ID, group-ID are documented in :doc:`fix <fix>` command
* style = *pimdb/langevin* or *pimdb/nvt* = style name of this fix command
* zero or more keyword/value pairs may be appended
* keywords for style *pimdb/nvt*

  .. parsed-literal::
       *keywords* = *method* or *fmass* or *sp* or *temp* or *nhc*
       *method* value = *pimd* or *nmpimd*
       *fmass* value = scaling factor on mass
       *sp* value = scaling factor on Planck constant
       *temp* value = temperature (temperature units)
       *nhc* value = Nc = number of chains in Nose-Hoover thermostat

* keywords for style *pimdb/langevin*

  .. parsed-literal::
       *keywords* = *integrator* or *ensemble* or *fmass* or *temp* or *thermostat* or *tau* or *fixcom* or *lj* or *esych*
       *integrator* value = *obabo* or *baoab*
       *ensemble* value = *nvt* or *nve*
       *fmass* value = scaling factor on mass
       *temp* value = temperature (temperature unit)
          temperature = target temperature of the thermostat
       *thermostat* values = style seed
          style value = *PILE_L*
          seed = random number generator seed
       *tau* value = thermostat damping parameter (time unit)
       *fixcom* value = *yes* or *no*
       *lj* values = epsilon sigma mass planck mvv2e
          epsilon = energy scale for reduced units (energy units)
          sigma = length scale for reduced units (length units)
          mass = mass scale for reduced units (mass units)
          planck = Planck's constant for other unit style
          mvv2e = mass * velocity^2 to energy conversion factor for other unit style
       *esynch* value = *yes* or *no*

Examples
""""""""

.. code-block:: LAMMPS

   fix 1 all pimdb/nvt method pimd fmass 1.0 sp 1.0 temp 2.0 nhc 4
   fix 1 all pimdb/langevin integrator obabo temp 113.15 thermostat PILE_L 1234 tau 1.0

Description
"""""""""""

These fix commands are based on the fixes :doc:`pimd/nvt and pimd/langevin <fix_pimd>` for 
performing quantum molecular dynamics simulations based
on the Feynman path-integral formalism. The key difference is that fix *pimd/nvt* and fix *pimd/langevin* simulate *distinguishable* particles,
while fix *pimdb/nvt* and fix *pimdb/langevin* perform simulations of bosons, including exchange effects.
The *pimdb* commands share syntax with the equivalent *pimd* commands. The user is referred to the documentation of the *pimd* fix for a 
detailed syntax description and additional, general capabilities of the commands.
The major differences from fix *pimd* in terms of capabilities are:

* Fix *pimdb/nvt* the only supports the "pimd" and "nmpimd" methods. Fix *pimdb/langevin* only supports the "pimd" method, which is the default in this fix. These restrictions are related to the use of normal modes, which change in bosons. For similar reasons, *fmmode* of *pimd/langevin* should not be used, and would raise an error if set to a value other than *physical*.
* Fix *pimdb/langevin* currently does not support *ensemble* other than *nve*, *nvt*. The barostat related keywords *iso*, *aniso*, *barostat*, *taup* are not supported.
* Fix *pimdb/langevin* also has a keyword not available in fix *pimd/langevin*: *esynch*, with default *yes*. If set to *no*, some time consuming synchronization of spring energies and
the primitive kinetic energy estimator between processors is avoided.

The isomorphism between the partition function of :math:`N` bosonic quantum particles and that of a system of classical ring polymers
at inverse temperature :math:`\beta`
is given by :ref:`(Tuckerman) <book-Tuckerman>`:

.. math::

   Z \propto \int d{\bf q} \cdot \frac{1}{N!} \sum_\sigma \textrm{exp} [ -\beta \left( E^\sigma + V \right) ].

Here, :math:`V` is the potential between different particles at the same imaginary time slice, which is the same for bosons and
distinguishable particles. The sum is over all permutations :math:`\sigma`. Recall that a permutation matches each element :math:`l` in :math:`1, ..., N` to an element :math:`\sigma(l)` in :math:`1, ..., N` without repetitions. The energies :math:`E^\sigma` correspond to the linking of ring polymers of different particles according to the permutations:

.. math::

   E^\sigma = \frac{mP}{2\beta^2 \hbar^2} \sum_{\ell=1}^N \sum_{j=1}^P \left(\mathbf{q}_\ell^j - \mathbf{q}_\ell^{j+1}\right)^2,

where :math:`P` is the number of beads and :math:`\mathbf{q}_\ell^{P+1}=\mathbf{q}_{\sigma(\ell)}^1.` 

Hirshberg et. al. showed that the ring polymer potential 
:math:`-\frac{1}{\beta}\textrm{ln}\left[ \frac{1}{N!} \sum_\sigma e ^ { -\beta  E^\sigma } \right]`, which scales exponentially with :math:`N`, 
can be replaced by a potential :math:`V^{[1,N]}` defined through a recurrence relation :ref:`(Hirshberg1) <Hirshberg>`:

.. math::

   e ^ { -\beta  V^{[1,N]} } = \frac{1}{N} \sum_{k=1}^N e ^ { -\beta \left(  V^{[1,N-k]} + E^{[N-K+1,N]} \right)}.

Here, :math:`E^{[N-K+1,N]}` is the spring energy of the ring polymer obtained by connecting the beads of particles :math:`N − k + 1, N − k + 2, ..., N` in a cycle.
This potential does not include all :math:`N!` permutations, but samples the same bosonic partition function. The implemented algorithm in LAMMPS for calculating 
the potential is the one developed by Feldman and Hirshberg, which scales like :math:`N^2+PN` :ref:`(Feldman) <Feldman>`. 
The forces are calculated as weighted averages over the representative permutations,
through an algorithm that scales the same as the one for the potential calculation, :math:`N^2+PN` :ref:`(Feldman) <Feldman>`.

Restart, fix_modify, output, run start/stop, minimize info
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

The use of :doc:`binary restart files <restart>` and :doc:`fix_modify <fix_modify>` is the same as in :doc:`fix pimd <fix_pimd>`.

Fix *pimdb/nvt* computes a global 4-vector, which can be accessed by
various :doc:`output commands <Howto_output>`.  The quantities in
the global vector are:

   #. the total spring energy of the quasi-beads,
   #. the current temperature of the classical system of ring polymers,
   #. the current value of the scalar virial estimator for the kinetic
      energy of the quantum system :ref:`(Herman) <HermanBB>` (see the justification in the supporting information of :ref:`(Hirshberg2) <HirshbergInvernizzi>`),
   #. the current value of the scalar primitive estimator for the kinetic
      energy of the quantum system :ref:`(Hirshberg1) <Hirshberg>`.

The vector values calculated by fix *pimdb/nvt* are "extensive", except for the
temperature, which is "intensive". 

Fix *pimdb/langevin* computes a global 6-vector, which
can be accessed by various :doc:`output commands <Howto_output>`. The quantities in the global vector are:

   #. kinetic energy of the beads,
   #. spring elastic energy of the beads,
   #. potential energy of the bead,
   #. total energy of all beads (conserved if *ensemble* is *nve*)
   #. primitive kinetic energy estimator :ref:`(Hirshberg1) <Hirshberg>`
   #. virial energy estimator :ref:`(Herman) <HermanBB>` (see the justification in the supporting information of :ref:`(Hirshberg2) <HirshbergInvernizzi>`).

The first three are different for different log files, and the others are the same for different log files,
except for the primitive kinetic energy estimator when setting *esynch* to *no*. Then, the primitive kinetic energy estimator is obtained by summing over all log files.
Also note that when *esynch* is set to *no*, the fourth output gives the total energy of all beads excluding the spring elastic energy, 
which can be obtained from the second output by summing over all log files.
All vector values calculated by fix *pimdb/langevin* are "extensive".

For both *pimdb/nvt* and *pimdb/langevin*, the contribution of the exterior spring to the primitive estimator is printed to the first log file.
The contribution of the :math:`P-1` interior springs is printed to the other :math:`P-1` log files.
The contribution of the constant :math:`\frac{PdN}{2 \beta}` (with :math:`d` being the dimentionality) is equally divided over log files.
Restrictions
""""""""""""

These fixes are part of the REPLICA package.  They are only enabled if
LAMMPS was built with that package.  See the :doc:`Build package
<Build_package>` page for more info.

The restrictions of :doc:`fix pimd <fix_pimd>` apply.

Default
"""""""

The keyword defaults for fix *pimdb/nvt* are method = pimd, fmass = 1.0, sp
= 1.0, temp = 300.0, and nhc = 2.

The keyord defaults for fix *pimdb/langevin* are integrator = obabo, method = pimd, ensemble = nvt, fmass = 1.0,
temp = 298.15, thermostat = PILE_L, tau = 1.0, fixcom = yes, esynch = yes, and lj = 1 for all its arguments.
----------

.. _book-Tuckerman:

**(Tuckerman)** M. Tuckerman, Statistical Mechanics: Theory and Molecular Simulation (Oxford University Press, 2010)

.. _Hirshberg:

**(Hirshberg1)** B. Hirshberg, V. Rizzi, and M. Parrinello, “Path integral molecular dynamics for bosons,” Proc. Natl. Acad. Sci. U. S. A. 116, 21445 (2019)

.. _HirshbergInvernizzi:

**(Hirshberg2)** B. Hirshberg, M. Invernizzi, and M. Parrinello, “Path integral molecular dynamics for fermions: Alleviating the sign problem with the Bogoliubov inequality,” J Chem Phys, 152, 171102 (2020)

.. _Feldman:

**(Feldman)** Y. M. Y. Feldman and B. Hirshberg, “Quadratic scaling bosonic path integral molecular dynamics,” J. Chem. Phys. 159, 154107 (2023)

.. _HermanBB:

**(Herman)** M. F. Herman, E. J. Bruskin, B. J. Berne, J Chem Phys, 76, 5150 (1982).
