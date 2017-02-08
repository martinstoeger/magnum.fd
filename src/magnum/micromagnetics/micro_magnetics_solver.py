# Copyright 2012-2014 by the MicroMagnum Team
# Copyright 2014 by the magnum.fd Team
#
# This file is part of magnum.fd.
# magnum.fd is based heavily on MicroMagnum.
# (https://github.com/MicroMagnum/MicroMagnum)
#
# magnum.fd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# magnum.fd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with magnum.fd. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

from numpy.linalg import norm
import math
import numpy as np

import magnum.tools as tools
import magnum.solver as solver

from magnum.micromagnetics.io import writeOMF
from magnum.micromagnetics.stephandler import ScreenLog, ScreenLogMinimizer
from magnum.mesh import VectorField


class MicroMagneticsSolver(solver.Solver):
    def __init__(self, system, evolver, world):
        super(MicroMagneticsSolver, self).__init__(system, evolver)
        self.__world = world

    def __repr__(self):
        return "MicroMagneticsSolver@%s" % hex(id(self))

    world = property(lambda self: self.__world)

    def relax(self, *args, **kwargs):
        # catch CVode, when using relax condition
        if self.evolver.__class__.__name__ == "Cvode":
          raise Exception("CVode is not usable to relax a system, yet. Please use rkf45.")

        return self.solve(solver.condition.Relaxed(*args, **kwargs))


    def simple_minimize(self):
        print("start simple_minimize")

        # step size
        h = 1e-14

        # stop criterion
        dE = 1e1
        E0 = 1e99
        E1 = 1e98

        # screen logger
        log = ScreenLogMinimizer()

        # deg_per_ns_minimizer was missing for logger
        dpns = 1.
        self.state.deg_per_ns_minimizer = dpns

        # Reset step
        self.state.step = 0

        while abs(E0 - E1) > dE:
            dM = self.state.minimizer_dM
            dM = dM.to_numpy()

            M_next = self.state.y
            M_next = M_next.to_numpy()
            M_next += h * dM

            self.state.y.from_numpy(M_next)
            self.state.finish_step()
            self.state.flush_cache()

            E0 = E1
            E1 = self.state.E_tot

            # log
            if (self.state.step % 100 == 0):
                log.handle(self.state)

            # Update step
            self.state.step += 1

            if (self.state.step % 100 == 0):
                test = self.state.y.to_numpy()

    def minimize(self, max_dpns = 0.01, samples = 10, h_max = 1e-5, h_min = 1e-16):
        """
        Minimizes the energy with a direct minimization strategy.
        """
        counter = 0
        # TODO make use of stephandlers for logging
        h        = self.state.h
        dpnslist = []
        log      = ScreenLogMinimizer()

        # Reset step
        self.state.step = 0

        while len(dpnslist) < samples or max(dpnslist) > max_dpns:
            # Calculate next M and dM for minimization step
            M_next = self.state.minimizer_M(h)
            dM = self.state.minimizer_dM
            counter += 2

            # Get s^n-1 for step-size calculation
            M_diff = VectorField(self.mesh)
            M_diff.assign(M_next)
            M_diff.add(self.state.M, -1.0)

            # Set next M
            self.state.y = M_next
            self.state.finish_step() # normalize, TODO really need to do this every step?
            self.state.flush_cache()

            # Calculate deg per ns
            # TODO M.absMax might be the wrong choice if different materials are in use
            dp_timestep = (180.0 / math.pi) * math.atan2(M_diff.absMax(), self.state.M.absMax())
            dpns = abs(1e-9 * dp_timestep / h)
            dpnslist.append(dpns)
            if len(dpnslist) > samples: dpnslist.pop(0)
            self.state.deg_per_ns_minimizer = dpns

            # Get y^n-1 for step-size calculation
            dM_diff = VectorField(self.mesh)
            dM_diff.assign(self.state.minimizer_dM)
            dM_diff.add(dM, -1.0)

            # Next stepsize (Alternate h1 and h2)
            try:
              if (self.state.step % 2 == 0):
                h = M_diff.dotSum(M_diff) / M_diff.dotSum(dM_diff)
              else:
                h = M_diff.dotSum(dM_diff) / dM_diff.dotSum(dM_diff)
            except ZeroDivisionError, ex:
              h = h_max

            h_sign = math.copysign(1, h)
            h = max(min(abs(h), h_max), h_min) * h_sign

            if (self.state.step % 100 == 0):
              log.handle(self.state)

            # Update step
            self.state.step += 1
        return counter

    def handle_sigint(self):
        print()

        text = ""
        text += "State:\n"
        text += "       step = %s\n" % self.state.step
        text += "          t = %s\n" % self.state.t
        text += "     avg(M) = %s\n" % (self.state.M.average(),)
        text += " deg_per_ns = %s\n" % self.state.deg_per_ns
        text += "\n"
        text += "Mesh: %s\n" % self.mesh
        text += "\n"
        text += "Options:"

        loggers = [h for (h, _) in self.step_handlers if isinstance(h, ScreenLog)]

        answer = tools.interactive_menu(
            header="Solver interrupted by signal SIGINT (ctrl-c)",
            text=text,
            options=[
                "Continue",
                "Stop solver and return the current state as the result",
                "Save current magnetization to .omf file, then continue",
                "Raise KeyboardInterrupt",
                "Kill program",
                "Start debugger",
                "Toggle console log (now:%s)" % ("enabled" if loggers else "disabled")
            ]
        )
        if answer == 1:
            return
        elif answer == 2:
            raise solver.Solver.FinishSolving()
        elif answer == 3:
            print("Enter file name ('.omf' is appended automatically)")
            path = tools.getline() + ".omf"
            writeOMF(path, self.state.M)
            print("Done.")
            return False
        elif answer == 4:
            raise KeyboardInterrupt()
        elif answer == 5:
            import sys
            sys.exit(-1)
        elif answer == 6:
            raise solver.Solver.StartDebugger()
        elif answer == 7:
            if loggers:
                for logger in loggers:
                    self.removeStepHandler(logger)
                print("Disabled console log.")
            else:
                from magnum.solver.condition import EveryNthStep
                self.addStepHandler(ScreenLog(), EveryNthStep(100))
                print("Enabled console log.")
            return
        assert False


    ##############################################################################
    def minimize_BB(self, vol):
        eps = 2.22e-16  # DBL_EPSILON
        MU0 = 1.2566e-6
        counter = [0]
        def minimize(vol):
            print("start advanced_minimize")

            #one dim numpy array
            x0 = self.state.M
            x0 = x0.to_numpy().flatten()
            x0 = x0                                                                   # * mu0
            self.state.M.from_numpy(x0)
            self.state.flush_cache()

            #flos_minimizer._minimize_np(M_next, dM)#############################

            #renorm_np = None
            def renorm_np(arg):
                self.state.M.from_numpy(arg)
                self.state.finish_step()
                self.state.flush_cache()
                #print "renorm",norm(self.state.M.to_numpy().flatten())**2
                return self.state.M.to_numpy().flatten()


            def obj_grad_np(arg, counter):
                self.state.M.from_numpy(arg)
                #print "m", self.state.M.to_numpy().flatten()
                self.state.flush_cache()
                grad = self.state.minimizer_dM_minimize_BB.to_numpy().flatten()
                f    = self.state.E_minimize_BB
                counter[0] += 2
                #print "f, grad", f, norm(grad)*((L/N)**(3) * MU0 / 8.e5**2)
                return f, grad * (vol * MU0 / 8.e5**2) * 1.e28

            log_np = None
            maxiter = 229                      #200 229 till convergence
            tol = 1e-6  #6
            m = 5

            ##################### start flos function
            sVector = np.zeros((x0.size, m))
            yVector = np.zeros((x0.size, m))
            alpha = np.zeros(m)

            f, grad = obj_grad_np(x0, counter)

            H0k = 1.
            if renorm_np is not None:
                x0 = renorm_np(x0)
            n = 0
            for globIter in range(maxiter):
                #print "Here starts the %d. loop!!!" % globIter
                # update history
                f0 = f
                x_old = x0
                grad_old = grad

                # Algorithm 7.4 (L-BFGS two-loop recursion)
                q = grad.copy()
                k = min(m, n)

                # for i = k-1, k-2, ... , k-m
                for i in range(k - 1, -1, -1):
                    rho = 1. / sVector[:, i].dot(yVector[:, i])
                    alpha[i] = rho * sVector[:, i].dot(q)
                    q -= alpha[i] * yVector[:, i]

                # r <- H_k^0*q
                q = H0k * q

                # for i = k-m, k-m+1, ... , k-1
                for i in range(0, k):
                    rho = 1. / sVector[:, i].dot(yVector[:, i])
                    beta = rho * yVector[:, i].dot(q)
                    q += sVector[:, i] * (alpha[i] - beta)
                # stop with result "H_k*f_f'=q"

                # any issues with the descent direction?
                descent = -grad.dot(q)
                if descent > -1e-15:
                    q = grad.copy()
                    n = 0
                    print("Had to fix descent direction!!!(descent=%e, |g|=%e, |q|=%e)" % (
                    descent, norm(grad, ord=np.inf), norm(q, ord=np.inf)))                                                 #warning

                # find steplength
                x0, f, grad, rate = _linesearch(f, x0, grad, -q, tol, obj_grad_np, renorm_np)                               #changed self._linesearch

                s = x0 - x_old
                #print "s",s
                y = grad - grad_old

                if _check_convergence_np(f, f0 - f, x0, s, grad, rate, tol) == True:
                    break

                # update the history
                if math.fabs(s.dot(y)) > math.sqrt(eps) * norm(y) * norm(s):  # Dennis, Schnabel 9.4.1
                    if n < m:
                        sVector[:, n] = s
                        yVector[:, n] = y
                        n += 1
                    else:
                        sVector[:, :-1] = sVector[:, 1:]
                        sVector[:, -1] = s
                        yVector[:, :-1] = yVector[:, 1:]
                        yVector[:, -1] = y
                    H0k = y.dot(s) / y.dot(y)
                else:
                    print("Minimizer_LBFGS: skip updated to avoid singular hessian approximation!")                         #warning

                # output some infos
                #if log_np is not None:
                #    log_np(x0)

            if globIter + 1 == maxiter:
                print("Minimizer_LBFGS: not converged after maxiter(%d) iterations!" % maxiter)                             #warninig

            info = {'iter': globIter}
            #print counter
            return x0, info, counter


        def _check_convergence_np(f, df, x, dx, grad, rate, tol):                                                           #self out of variable list
            x_norm = norm(x, ord=np.inf)
            g_norm = norm(grad, ord=np.inf)
            dx_norm = norm(dx, ord=np.inf)

            print("Minimizer: f: %e,   df: %e < %e,   dx: %e < %e,   |g|: %e < %e,   rate: %e" % (
            f, math.fabs(df), tol * (1. + math.fabs(f)), dx_norm, math.sqrt(tol) * (1. + math.fabs(f)), g_norm,
            pow(tol, 1. / 3.) * (1. + math.fabs(f)), rate))                                                                     #info

            if g_norm < eps * (1. + math.fabs(f)):
                print("Minimizer: Convergence reached1!")                                                                      #info
                return True

            if math.fabs(df) < tol * (1. + math.fabs(f)) and dx_norm < math.sqrt(tol) * (1. + x_norm) and g_norm < pow(tol, 1. / 3.) * (
                1. + math.fabs(f)):
                print("Minimizer: Convergence reached2!")                                                                    #info
                return True
            return False


        def _linesearch(f, x0, g, s, tol, obj_grad_np, renorm_np=None):                                         #self out of variable list
            # we rewrite this from MIN-LAPACK and some MATLAB code
            stp = 1.
            info = 0
            infoc = 1
            xtol = 1e-15
            ftol = 1e-4  # c1
            gtol = 0.9  # c2
            stpmin = 1e-15
            stpmax = 1e15
            xtrapf = 4
            maxfev = 30  # 200 #20
            nfev = 0

            dginit = g.dot(s)
            if dginit >= 0.0:
                raise RuntimeError("Search direction s no descent direction(dginit=%e)! This should not happen!!" % dginit)

            brackt = False
            stage1 = True

            finit = f
            dgtest = ftol * dginit
            width = stpmax - stpmin
            width1 = 2 * width

            stx = 0.0
            fx = finit
            dgx = dginit
            sty = 0.0
            fy = finit
            dgy = dginit

            while True:
                # make sure we stay in the interval when setting min/max-step-width
                if brackt:
                    stmin = min(stx, sty)
                    stmax = max(stx, sty)
                else:
                    stmin = stx
                    stmax = stp + xtrapf * (stp - stx)

                # Force the step to be within the bounds stpmax and stpmin.
                stp = max(stp, stpmin)
                stp = min(stp, stpmax)

                # Oops, let us return the last reliable values
                if ((brackt and ((stp <= stmin) or (stp >= stmax))) or (nfev >= maxfev - 1) or (infoc == 0) or (
                    brackt and ((stmax - stmin) <= (xtol * stmax)))):
                    stp = stx

                # test new point
                # TODO: test norm conserving update!?
                x = x0 + stp * s
                if renorm_np is not None:
                    x = renorm_np(x)
                f, g = obj_grad_np(x,counter)   #counter zugefuegt
                nfev += 1
                dg = g.dot(s)
                ftest1 = finit + stp * dgtest
                ftest2 = finit + tol * math.fabs(finit)
                ft = 2 * ftol - 1

                # all possible convergence tests
                if (brackt and ((stp <= stmin) or (stp >= stmax))) or (infoc == 0):
                    info = 6

                # if (stp == stpmax) and (f <= ftest1) and (dg <= dgtest):
                if (stp == stpmax) and (f <= ftest2) and (dg <= dgtest):
                    info = 5

                # if (stp == stpmin) and ((f > ftest1) or (dg >= dgtest)):
                if (stp == stpmin) and ((f > ftest2) or (dg >= dgtest)):
                    info = 4

                if nfev >= maxfev:
                    info = 3
                    stp = 1.
                    print("Minimizer_LBFGS: linesearch did not converge!")                                                   #warning

                if brackt and (stmax - stmin <= xtol * stmax):
                    info = 2

                if (f <= ftest1) and (math.fabs(dg) <= gtol * (-dginit)):
                    info = 1

                if (f <= ftest2) and (ft * dginit >= dg) and (math.fabs(dg) <= gtol * (-dginit)):
                    info = 1

                # terminate when convergence reached
                if info != 0:
                    return x, f, g, stp

                # if stage1 and (f <= ftest1) and (dg >= min(ftol, gtol)*dginit):
                if stage1 and (f <= ftest2) and (dg >= min(ftol, gtol) * dginit):  # approx wolfe 1
                    stage1 = False

                # if stage1 and (f <= fx) and (f > ftest1):
                if stage1 and (f <= fx) and not (f <= ftest2 and ft * dginit >= dg):
                    fm = f - stp * dgtest
                    fxm = fx - stx * dgtest
                    fym = fy - sty * dgtest
                    dgm = dg - dgtest
                    dgxm = dgx - dgtest
                    dgym = dgy - dgtest

                    stx, fxm, dgxm, sty, fym, dgym, stp, fm, dgm, brackt, stmin, stmax, infoc = _cstep(stx, fxm, dgxm,
                                                                                                            sty, fym, dgym,
                                                                                                            stp, fm, dgm,
                                                                                                            brackt, stmin,
                                                                                                            stmax, infoc)

                    fx = fxm + stx * dgtest
                    fy = fym + sty * dgtest
                    dgx = dgxm + dgtest
                    dgy = dgym + dgtest
                else:
                    # this is ugly and some variables should be moved to the class scope
                    stx, fx, dgx, sty, fy, dgy, stp, f, dg, brackt, stmin, stmax, infoc = _cstep(stx, fx, dgx, sty, fy,
                                                                                                      dgy, stp, f, dg,
                                                                                                      brackt, stmin, stmax,
                                                                                                      infoc)                        #self._cstep

                if brackt:
                    if math.fabs(sty - stx) >= 0.66 * width1:
                        stp = stx + 0.5 * (sty - stx)
                    width1 = width
                    width = math.fabs(sty - stx)

        def _cstep(stx, fx, dx, sty, fy, dy, stp, fp, dp, brackt, stpmin, stpmax, info):                                #self out of variable list
            info = 0
            bound = False

            # Check the input parameters for errors.
            if (brackt and ((stp <= min(stx, sty)) or (stp >= max(stx, sty)))) or (dx * (stp - stx) >= 0.0) or (
                stpmax < stpmin):
                raise RuntimeError("Check of input parameters failed")

            sgnd = dp * (dx / math.fabs(dx))
            stpf = 0
            stpc = 0
            stpq = 0

            if fp > fx:
                info = 1
                bound = True
                theta = 3. * (fx - fp) / (stp - stx) + dx + dp
                s = max(theta, max(dx, dp))
                gamma = s * math.sqrt((theta / s) * (theta / s) - (dx / s) * (dp / s))
                if stp < stx:
                    gamma = -gamma
                p = (gamma - dx) + theta
                q = ((gamma - dx) + gamma) + dp
                r = p / q
                stpc = stx + r * (stp - stx)
                stpq = stx + ((dx / ((fx - fp) / (stp - stx) + dx)) / 2.) * (stp - stx)
                if math.fabs(stpc - stx) < math.fabs(stpq - stx):
                    stpf = stpc
                else:
                    stpf = stpc + (stpq - stpc) / 2
                brackt = True
            elif sgnd < 0.0:
                info = 2
                bound = False
                theta = 3 * (fx - fp) / (stp - stx) + dx + dp
                s = max(theta, max(dx, dp))
                gamma = s * math.sqrt((theta / s) * (theta / s) - (dx / s) * (dp / s))
                if stp > stx:
                    gamma = -gamma

                p = (gamma - dp) + theta
                q = ((gamma - dp) + gamma) + dx
                r = p / q
                stpc = stp + r * (stx - stp)
                stpq = stp + (dp / (dp - dx)) * (stx - stp)
                if math.fabs(stpc - stp) > math.fabs(stpq - stp):
                    stpf = stpc
                else:
                    stpf = stpq
                brackt = True
            elif math.fabs(dp) < math.fabs(dx):
                info = 3
                bound = True
                theta = 3 * (fx - fp) / (stp - stx) + dx + dp
                s = max(theta, max(dx, dp))
                gamma = s * math.sqrt(max(0., (theta / s) * (theta / s) - (dx / s) * (dp / s)))
                if stp > stx:
                    gamma = -gamma
                p = (gamma - dp) + theta
                q = (gamma + (dx - dp)) + gamma
                r = p / q
                if (r < 0.0) and (gamma != 0.0):
                    stpc = stp + r * (stx - stp)
                elif stp > stx:
                    stpc = stpmax
                else:
                    stpc = stpmin
                stpq = stp + (dp / (dp - dx)) * (stx - stp)
                if brackt:
                    if math.fabs(stp - stpc) < math.fabs(stp - stpq):
                        stpf = stpc
                    else:
                        stpf = stpq
                else:
                    if math.fabs(stp - stpc) > math.fabs(stp - stpq):
                        stpf = stpc
                    else:
                        stpf = stpq
            else:
                info = 4
                bound = False
                if brackt:
                    theta = 3 * (fp - fy) / (sty - stp) + dy + dp
                    s = max(theta, max(dy, dp))
                    gamma = s * math.sqrt((theta / s) * (theta / s) - (dy / s) * (dp / s))
                    if stp > sty:
                        gamma = -gamma

                    p = (gamma - dp) + theta
                    q = ((gamma - dp) + gamma) + dy
                    r = p / q
                    stpc = stp + r * (sty - stp)
                    stpf = stpc
                elif stp > stx:
                    stpf = stpmax
                else:
                    stpf = stpmin

            if fp > fx:
                sty = stp
                fy = fp
                dy = dp
            else:
                if sgnd < 0.0:
                    sty = stx
                    fy = fx
                    dy = dx

                stx = stp
                fx = fp
                dx = dp

            stpf = min(stpmax, stpf)
            stpf = max(stpmin, stpf)
            stp = stpf

            if brackt and bound:
                if sty > stx:
                    stp = min(stx + 0.66 * (sty - stx), stp)
                else:
                    stp = max(stx + 0.66 * (sty - stx), stp)

            return [stx, fx, dx, sty, fy, dy, stp, fp, dp, brackt, stpmin, stpmax, info]
        return minimize(vol)

