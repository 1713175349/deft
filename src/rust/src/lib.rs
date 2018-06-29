extern crate internment;
extern crate tinyset;

use internment::Intern;
use tinyset::{Map64, Fits64};
use tinyset::u64set::Map64Iter;
use std::fmt::Debug;
use std::hash::Hash;
use std::iter::FromIterator;
use std::ops::Deref;
use std::any::Any;

#[derive(Debug, Eq, PartialEq)]
pub enum GenericExpr {
    Scalar(Expr<Scalar>),
    RealSpaceScalar(Expr<RealSpaceScalar>),
    KSpaceScalar(Expr<KSpaceScalar>),
}

impl GenericExpr {
    fn find(self, needle: GenericExpr) -> Option<GenericExpr> {
        if self == needle {
            return Some(self);
        }
        match self {
            GenericExpr::Scalar(s) =>
                match s.inner.deref() {
                    Scalar::Log(a) | Scalar::Exp(a) => GenericExpr::Scalar(*a).find(needle),
                    Scalar::Add(ref m) | Scalar::Mul(ref m) => m.iter().map(|(k, &_)| k.to_generic()).find(|k| *k == self),
                    Scalar::Integrate(_, b) => GenericExpr::RealSpaceScalar(*b).find(needle),
                    _ => None,
                },
            GenericExpr::RealSpaceScalar(rs) =>
                match rs.inner.deref() {
                    RealSpaceScalar::Log(a) | RealSpaceScalar::Exp(a) => GenericExpr::RealSpaceScalar(*a).find(needle),
                    RealSpaceScalar::Add(ref m) | RealSpaceScalar::Mul(ref m) => m.iter().map(|(k, &_)| k.to_generic()).find(|k| *k == self),
                    RealSpaceScalar::IFFT(b) => GenericExpr::KSpaceScalar(*b).find(needle),
                    _ => None,
                },
            GenericExpr::KSpaceScalar(ks) =>
                match ks.inner.deref() {
                    KSpaceScalar::Log(a) | KSpaceScalar::Exp(a) => GenericExpr::KSpaceScalar(*a).find(needle),
                    KSpaceScalar::Add(ref m) | KSpaceScalar::Mul(ref m) => m.iter().map(|(k, &_)| k.to_generic()).find(|k| *k == self),
                    KSpaceScalar::FFT(b) => GenericExpr::RealSpaceScalar(*b).find(needle),
                    _ => None,
                },
        }
    }
}

pub trait ExprType: 'static + Send + Clone + Eq + Debug + Hash {
    fn cpp(&self) -> String;
    fn contains_fft(&self) -> Vec<Expr<RealSpaceScalar>>;
    fn map_leaves<F: Fn(&Expr<Self>) -> Expr<Self>>(x: &Expr<Self>, f: F) -> Expr<Self>;
    fn to_generic(self) -> GenericExpr;
}

#[derive(Clone, Debug, Eq, Hash)]
pub struct Expr<T: ExprType> {
    inner: Intern<T>,
}

pub enum Stmt {
    AllocKSpaceScalar(String, Expr<KSpaceScalar>),
    AllocRealSpaceScalar(String, Expr<RealSpaceScalar>),
    AllocScalar(String, Expr<Scalar>),
}

impl Stmt {
    fn alloc_k_space_scalar<T: Into<String>>(s: T, e: Expr<KSpaceScalar>) -> Stmt {
        Stmt::AllocKSpaceScalar(s.into(), e)
    }

    fn alloc_real_space_scalar<T: Into<String>>(s: T, e: Expr<RealSpaceScalar>) -> Stmt {
        Stmt::AllocRealSpaceScalar(s.into(), e)
    }

    fn alloc_scalar<T: Into<String>>(s: T, e: Expr<Scalar>) -> Stmt {
        Stmt::AllocScalar(s.into(), e)
    }

    fn cpp(&self) -> String {
        match self {
            &Stmt::AllocKSpaceScalar(ref s, ref e) => {
                match e.inner.deref() {
                    KSpaceScalar::Var(v) => {
                        if s == v.deref() {
                            String::from("ComplexVector ")
                                + &s + &"(Nx*Ny*(int(Nz)/2+1);"
                        } else {
                            panic!("Tried to allocate a KSpaceScalar under a different name");
                        }
                    },
                    _ =>
                        String::from("ComplexVector ") + &s
                        + &"(Nx*Ny*(int(Nz)/2+1);\nfor (int i=0; i<Nx*Ny*Nz; i++) {\n"
                        + &s + &"[i] = " + &e.cpp() + &";\n}",
                }
            }
            &Stmt::AllocRealSpaceScalar(ref s, ref e) =>
                String::from("Vector") + &s
                + &"(Nx*Ny*Nz);\nfor (int i=0; i<Nx*Ny*Nz; i++) {\n"
                + &s + &"[i] = " + &e.cpp() + &";\n}",
            &Stmt::AllocScalar(ref s, ref e) =>
                String::from("double ") + &s + &" = " + &e.cpp() + &";\n",
        }
    }
}

fn test_stmt() {
    let k = Expr::new(&KSpaceScalar::var("k"));
    assert_eq!(Stmt::alloc_k_space_scalar("k", k).cpp(),
               "ComplexVector ktemp1(Nx*Ny*(int(Nz)/2+1));");
}

impl<T: ExprType> Expr<T> {
    fn new(inner: &T) -> Expr<T> {
        Expr { inner: Intern::new(inner.clone()), }
    }

    fn cpp(&self) -> String {
        self.inner.cpp()
    }

    fn cast<U: ExprType + From<T>>(&self) -> Expr<U> {
        Expr::new(&self.inner.deref().clone().into())
    }

    fn to_generic(self) -> GenericExpr {
        self.inner.deref().clone().to_generic()
    }
}

impl<T: ExprType, U: Clone + Into<Expr<T>>> PartialEq<U> for Expr<T> {
    fn eq(&self, other: &U) -> bool {
        self.inner == other.clone().into().inner
    }
}

impl<T: ExprType> Fits64 for Expr<T> {
    fn to_u64(self) -> u64 {
        self.inner.to_u64()
    }

    unsafe fn from_u64(x: u64) -> Self {
        Expr { inner: Intern::from_u64(x), }
    }
}

impl<T: ExprType> Copy for Expr<T> {}

impl<T: ExprAdd + ExprMul, N: Into<f64>> From<N> for Expr<T> {
    fn from(n: N) -> Self {
        let n = n.into();
        let inner = if n == 0.0 {
            T::zero()
        } else if n == 1.0 {
            T::one()
        } else {
            let mut map = AbelianMap::new();
            map.insert(Expr::new(&T::one()), n);
            T::sum_from_map(map)
        };
        Expr::new(&inner)
    }
}

pub trait ExprAdd: ExprType {
    fn sum_from_map(x: AbelianMap<Self>) -> Self;
    fn map_from_sum(&self) -> Option<&AbelianMap<Self>>;

    fn add(&self, other: &Self) -> Self {
        let mut sum: AbelianMap<Self>;
        match (self.map_from_sum(), other.map_from_sum()) {
            (Some(l), Some(r)) => {
                sum = l.clone();
                sum.union(r);
            },
            (Some(s), _) => {
                sum = s.clone();
                sum.insert(Expr::new(other), 1.0);
            },
            (_, Some(s)) => {
                sum = s.clone();
                sum.insert(Expr::new(self), 1.0);
            },
            (_, _) => {
                sum = AbelianMap::new();
                sum.insert(Expr::new(self), 1.0);
                sum.insert(Expr::new(other), 1.0);
            },
        }
        Self::sum_from_map(sum)
    }

    fn neg(&self) -> Self {
        match self.map_from_sum() {
            Some(ref map) =>
                Self::sum_from_map(map.iter().map(|(k, &v)| (k, -v)).collect()),
            _ => if *self == Self::zero() {
                    Self::zero()
                } else {
                    let mut map = AbelianMap::new();
                    map.insert(Expr::new(self), -1.0);
                    Self::sum_from_map(map)
                },
        }
    }

    fn zero() -> Self {
        Self::sum_from_map(AbelianMap::new())
    }
}

impl<T: ExprAdd, U: Into<Expr<T>>> std::ops::Add<U> for Expr<T> {
    type Output = Self;

    fn add(self, other: U) -> Self {
        let other = other.into();
        Expr::new(&self.inner.deref().add(other.inner.deref()))
    }
}

impl<T: ExprAdd, U: Into<Expr<T>>> std::ops::Sub<U> for Expr<T> {
    type Output = Self;

    fn sub(self, other: U) -> Self {
        let other = other.into();
        Expr::new(&self.inner.deref().add(&other.inner.deref().neg()))
    }
}

impl<T: ExprAdd> std::ops::Neg for Expr<T> {
    type Output = Self;

    fn neg(self) -> Self {
        Expr::new(&self.inner.deref().neg())
    }
}

pub trait ExprMul: ExprType {
    fn mul_from_map(x: AbelianMap<Self>) -> Self;
    fn map_from_mul(&self) -> Option<&AbelianMap<Self>>;

    fn mul(&self, other: &Self) -> Self {
        let mut prod: AbelianMap<Self>;
        match (self.map_from_mul(), other.map_from_mul()) {
            (Some(l), Some(r)) => {
                prod = l.clone();
                prod.union(r);
            },
            (Some(s), _) => {
                prod = s.clone();
                prod.insert(Expr::new(other), 1.0);
            },
            (_, Some(s)) => {
                prod = s.clone();
                prod.insert(Expr::new(self), 1.0);
            },
            (_, _) => {
                prod = AbelianMap::new();
                prod.insert(Expr::new(self), 1.0);
                prod.insert(Expr::new(other), 1.0);
            },
        }
        Self::mul_from_map(prod)
    }

    fn recip(&self) -> Self {
        match self.map_from_mul() {
            Some(ref map) =>
                Self::mul_from_map(map.iter().map(|(k, &v)| (k, -v)).collect()),
            _ => if *self == Self::one() {
                    Self::one()
                } else {
                    let mut map = AbelianMap::new();
                    map.insert(Expr::new(self), -1.0);
                    Self::mul_from_map(map)
                },
        }
    }

    fn one() -> Self {
        Self::mul_from_map(AbelianMap::new())
    }
}

impl<T: ExprMul, U: Into<Expr<T>>> std::ops::Mul<U> for Expr<T> {
    type Output = Self;

    fn mul(self, other: U) -> Self {
        let other = other.into();
        Expr::new(&self.inner.deref().mul(other.inner.deref()))
    }
}

impl<T: ExprMul, U: Into<Expr<T>>> std::ops::Div<U> for Expr<T> {
    type Output = Self;

    fn div(self, other: U) -> Self {
        let other = other.into();
        Expr::new(&self.inner.deref().mul(&other.inner.deref().recip()))
    }
}

macro_rules! impl_expr_add {
    ( $name:ident ) => {
        impl ExprAdd for $name {
            fn sum_from_map(map: AbelianMap<Self>) -> Self {
                if map.len() == 1 {
                    let (k, &v) = map.iter().next().unwrap();
                    if v == 1.0 {
                        return k.inner.deref().clone();
                    }
                }
                $name::Add(map)
            }

            fn map_from_sum(&self) -> Option<&AbelianMap<Self>> {
                if let &$name::Add(ref map) = self {
                    Some(&map)
                } else {
                    None
                }
            }
        }
    }
}

macro_rules! impl_expr_mul {
    ( $name:ident ) => {
        impl ExprMul for $name {
            fn mul_from_map(map: AbelianMap<Self>) -> Self {
                if map.len() == 1 {
                    let (k, &v) = map.iter().next().unwrap();
                    if v == 1.0 {
                        return k.inner.deref().clone();
                    }
                }
                $name::Mul(map)
            }

            fn map_from_mul(&self) -> Option<&AbelianMap<Self>> {
                if let &$name::Mul(ref map) = self {
                    Some(&map)
                } else {
                    None
                }
            }
        }
    }
}

#[derive(Clone, PartialEq, Eq, Debug, Hash)]
pub enum Scalar {
    Var(Intern<String>),
    Exp(Expr<Scalar>),
    Log(Expr<Scalar>),
    Add(AbelianMap<Scalar>),
    Mul(AbelianMap<Scalar>),
    Integrate(Intern<String>, Expr<RealSpaceScalar>),
}

impl_expr_add!(Scalar);
impl_expr_mul!(Scalar);
impl_expr_add!(RealSpaceScalar);
impl_expr_mul!(RealSpaceScalar);
impl_expr_add!(KSpaceScalar);
impl_expr_mul!(KSpaceScalar);

impl Scalar {
    fn exp(&self) -> Self { Scalar::Exp(Expr::new(self)) }
    fn log(&self) -> Self { Scalar::Exp(Expr::new(self)) }
    fn var(name: &str) -> Self { Scalar::Var(Intern::new(String::from(name))) }
}

impl ExprType for Scalar {
    fn to_generic(self) -> GenericExpr {
        GenericExpr::Scalar(Expr::new(&self))
    }

    fn cpp(&self) -> String {
        match self {
            &Scalar::Var(s) =>
                (*s).clone(),
            &Scalar::Exp(a) =>
                String::from("exp(") + &a.cpp() + &")",
            &Scalar::Log(a) =>
                String::from("log(") + &a.cpp() + &")",
            &Scalar::Add(ref m) => {
                let pcoeff = |&(ref x, ref c): &(String, f64)| -> String {
                    if x == "1" {
                        c.to_string()
                    } else if *c == 1.0 {
                        x.clone()
                    } else {
                        c.to_string() + &" * " + &x
                    }
                };
                let ncoeff = |&(ref x, ref c): &(String, f64)| -> String {
                    if x == "1" {
                        c.abs().to_string()
                    } else if *c == -1.0 {
                        x.clone()
                    } else {
                        c.abs().to_string() + &" * " + &x
                    }
                };
                let (p, n) = m.split_cpp_sort();
                match (p.len(), n.len()) {
                    (0, 0) =>
                        String::from("0"),
                    (_, 0) =>
                        p.iter().map(pcoeff).collect::<Vec<String>>().join(" + "),
                    (0, _) =>
                        String::from("-")
                            + &n.iter().map(ncoeff).collect::<Vec<String>>().join(" + "),
                    (_, _) =>
                        p.iter().map(pcoeff).collect::<Vec<String>>().join(" + ")
                            + &" - "
                            + &n.iter().map(ncoeff).collect::<Vec<String>>().join(" + "),
                }
            },
            &Scalar::Mul(ref m) => {
                let ref power = |&(ref x, ref p): &(String, f64)| -> String {
                    if x == "1" || p.abs() == 1.0 {
                        x.clone()
                    } else if p.abs() == 2.0 {
                        x.clone() + &" * " + &x
                    } else {
                        String::from("pow(") + &x + &", " + &p.abs().to_string() + &")"
                    }
                };
                let (n, d) = m.split_cpp_sort();
                match (n.len(), d.len()) {
                    (0, 0) =>
                        String::from("1"),
                    (_, 0) =>
                        n.iter().map(power).collect::<Vec<String>>().join(" * "),
                    (0, _) =>
                        String::from("1 / (")
                            + &d.iter().map(power).collect::<Vec<String>>().join(" * ")
                            + &")",
                    (_, _) =>
                        n.iter().map(power).collect::<Vec<String>>().join(" * ")
                            + &" / ("
                            + &d.iter().map(power).collect::<Vec<String>>().join(" * ")
                            + &")",
                }
            },
            &Scalar::Integrate(s, integrand) =>
                String::from("for (int i = 0, integrand = 0.0; i < Nx * Ny * Nz; i++)\n\t")
                    + &s.deref() + &" += " + &integrand.cpp() + &";\n",
        }
    }

    fn contains_fft(&self) -> Vec<Expr<RealSpaceScalar>> {
        match self {
            &Scalar::Var(_) =>
                Vec::new(),
            &Scalar::Exp(a) | &Scalar::Log(a)  =>
                a.inner.deref().contains_fft(),
            &Scalar::Integrate(_, a) =>
                a.inner.deref().contains_fft(),
            &Scalar::Add(ref m) | &Scalar::Mul(ref m) =>
                m.into_iter().flat_map(|(k, _)| k.inner.deref().contains_fft()).collect(),
        }
    }

    fn substitute<S: ExprType>(&self, old: Expr<S>, new: Expr<S>) -> Expr<Self> {
        match self {
            &Scalar::Integrate(dx,e) =>
                Expr::new(&Scalar::Integrate(dx, e.substitute(old,new))),
            &Scalar::Exp(a) =>
                Expr::new(&Scalar::Exp(a.substitute(old,new))),
            &Scalar::Log(a) =>
                Expr::new(&Scalar::Log(a.substitute(old,new))),
            &Scalar::Add(ref m) =>
                Expr::new(&Scalar::Add(AbelianMap::from_iter(m.into_iter().map(|(k, &v)| (k.substitute(old,new), v))))), // FIXME
            &Scalar::Mul(ref m) =>
                Expr::new(&Scalar::Mul(AbelianMap::from_iter(m.into_iter().map(|(k, &v)| (k.substitute(old,new), v))))), // FIXME
            _ => Expr::new(self)
        }
    }
    fn map_leaves(x: &Expr<Self>, f: impl Fn(&Expr<Self>) -> Expr<Self>) -> Expr<Self> {
        match x.inner.deref() {
            &Scalar::Var(_) | &Scalar::Integrate(_, _) =>
                f(x),
            &Scalar::Exp(a) =>
                Expr::new(&Scalar::Exp(f(&a))),
            &Scalar::Log(a) =>
                Expr::new(&Scalar::Log(f(&a))),
            &Scalar::Add(ref m) =>
                Expr::new(&Scalar::Add(AbelianMap::from_iter(m.into_iter().map(|(k, &v)| (f(&k), v))))),
            &Scalar::Mul(ref m) =>
                Expr::new(&Scalar::Mul(AbelianMap::from_iter(m.into_iter().map(|(k, &v)| (f(&k), v))))),
        }
    }
}

#[derive(Clone, PartialEq, Eq, Debug, Hash)]
pub enum RealSpaceScalar {
    Var(Intern<String>),
    ScalarVar(Intern<String>),
    Exp(Expr<RealSpaceScalar>),
    Log(Expr<RealSpaceScalar>),
    Add(AbelianMap<RealSpaceScalar>),
    Mul(AbelianMap<RealSpaceScalar>),
    IFFT(Expr<KSpaceScalar>),
}

impl RealSpaceScalar {
    fn exp(&self) -> Self { RealSpaceScalar::Exp(Expr::new(self)) }
    fn log(&self) -> Self { RealSpaceScalar::Exp(Expr::new(self)) }
    fn var(name: &str) -> Self { RealSpaceScalar::Var(Intern::new(String::from(name))) }
    fn scalar_var(name: &str) -> Self { RealSpaceScalar::ScalarVar(Intern::new(String::from(name))) }
    fn fft(&self) -> KSpaceScalar { KSpaceScalar::FFT(Expr::new(self)) }

    fn contains_ifft(&self) -> bool {
        match self {
            &RealSpaceScalar::IFFT(_) => true,
            &RealSpaceScalar::Var(_) | &RealSpaceScalar::ScalarVar(_) => false,
            &RealSpaceScalar::Exp(a) | &RealSpaceScalar::Log(a) => a.inner.deref().contains_ifft(),
            &RealSpaceScalar::Add(ref m) | &RealSpaceScalar::Mul(ref m) => m.into_iter().any(|(k, &_)| k.inner.deref().contains_ifft()),
        }
    }

    // in Expr<RSS> fn fix_top_level(&self) maybe?
}

impl ExprType for RealSpaceScalar {
    fn to_generic(self) -> GenericExpr {
        GenericExpr::RealSpaceScalar(Expr::new(&self))
    }

    fn cpp(&self) -> String {
        if !self.contains_ifft() {
            // match self.fake_scalar() { Ok(s) => same stuff, Err(todo) => { code to do todo first } }
            return String::from("Vector temp(Nx*Ny*Nz);\nfor (int i = 0; i < Nx * Ny * Nz; i++)\n\ttemp[i] = ") + &self.fake_scalar().cpp() + &"\n";
        }
        match self {
            &RealSpaceScalar::IFFT(a) =>
                match a.inner.deref() {
                    &KSpaceScalar::Var(s) =>
                        String::from("ifft(Nx, Ny, Nz, dV, ") + s.deref() + &")",
                    _ =>
                        String::from("ifft(Nx, Ny, Nz, dV, temp)"),
                }
            &RealSpaceScalar::Var(s) | &RealSpaceScalar::ScalarVar(s) =>
                (*s).clone(),
            &RealSpaceScalar::Exp(a) | &RealSpaceScalar::Log(a) =>
                a.cpp(),
            &RealSpaceScalar::Add(ref m) => {
                let pcoeff = |&(ref x, ref c): &(String, f64)| -> String {
                    if x == "1" {
                        c.to_string()
                    } else if *c == 1.0 {
                        x.clone()
                    } else {
                        c.to_string() + &" * " + &x
                    }
                };
                let ncoeff = |&(ref x, ref c): &(String, f64)| -> String {
                    if x == "1" {
                        c.abs().to_string()
                    } else if *c == -1.0 {
                        x.clone()
                    } else {
                        c.abs().to_string() + &" * " + &x
                    }
                };
                let (p, n) = m.split_cpp_sort();
                match (p.len(), n.len()) {
                    (0, 0) =>
                        String::from("0"),
                    (_, 0) =>
                        p.iter().map(pcoeff).collect::<Vec<String>>().join(" + "),
                    (0, _) =>
                        String::from("-")
                            + &n.iter().map(ncoeff).collect::<Vec<String>>().join(" + "),
                    (_, _) =>
                        p.iter().map(pcoeff).collect::<Vec<String>>().join(" + ")
                            + &" - "
                            + &n.iter().map(ncoeff).collect::<Vec<String>>().join(" + "),
                }
            },
            &RealSpaceScalar::Mul(ref m) => {
                let ref power = |&(ref x, ref p): &(String, f64)| -> String {
                    if x == "1" || p.abs() == 1.0 {
                        x.clone()
                    } else if p.abs() == 2.0 {
                        x.clone() + &" * " + &x
                    } else {
                        String::from("pow(") + &x + &", " + &p.abs().to_string() + &")"
                    }
                };
                let (n, d) = m.split_cpp_sort();
                match (n.len(), d.len()) {
                    (0, 0) =>
                        String::from("1"),
                    (_, 0) =>
                        n.iter().map(power).collect::<Vec<String>>().join(" * "),
                    (0, _) =>
                        String::from("1 / (")
                            + &d.iter().map(power).collect::<Vec<String>>().join(" * ")
                            + &")",
                    (_, _) =>
                        n.iter().map(power).collect::<Vec<String>>().join(" * ")
                            + &" / ("
                            + &d.iter().map(power).collect::<Vec<String>>().join(" * ")
                            + &")",
                }
            },
        }
    }

    fn contains_fft(&self) -> Vec<Expr<RealSpaceScalar>> {
        match self {
            &RealSpaceScalar::Var(_) | &RealSpaceScalar::ScalarVar(_) =>
                Vec::new(),
            &RealSpaceScalar::Exp(a) | &RealSpaceScalar::Log(a) =>
                a.inner.deref().contains_fft(),
            &RealSpaceScalar::IFFT(a) =>
                a.inner.deref().contains_fft(),
            &RealSpaceScalar::Add(ref m) | &RealSpaceScalar::Mul(ref m) =>
                m.into_iter().flat_map(|(k, _)| k.inner.deref().contains_fft()).collect(),
        }
    }

    fn substitute<S: ExprType>(&self, old: Expr<S>, new: Expr<S>) -> Expr<Self> {
        unimplemented!()
    }
    fn map_leaves(x: &Expr<Self>, f: impl Fn(&Expr<Self>) -> Expr<Self>) -> Expr<Self> {
        match x.inner.deref() {
            &RealSpaceScalar::Var(_) =>
                f(x),
            &RealSpaceScalar::ScalarVar(_) =>
                f(x),
            &RealSpaceScalar::Exp(a) =>
                Expr::new(&RealSpaceScalar::Exp(f(&a))),
            &RealSpaceScalar::Log(a) =>
                Expr::new(&RealSpaceScalar::Log(f(&a))),
            &RealSpaceScalar::IFFT(_) =>
                f(x),
            &RealSpaceScalar::Add(ref m) =>
                Expr::new(&RealSpaceScalar::Add(AbelianMap::from_iter(m.into_iter().map(|(k, &v)| (f(&k), v))))),
            &RealSpaceScalar::Mul(ref m) =>
                Expr::new(&RealSpaceScalar::Mul(AbelianMap::from_iter(m.into_iter().map(|(k, &v)| (f(&k), v))))),
        }
    }
}

#[derive(Clone, PartialEq, Eq, Debug, Hash)]
pub enum KSpaceScalar {
    Var(Intern<String>),
    ScalarVar(Intern<String>),
    Exp(Expr<KSpaceScalar>),
    Log(Expr<KSpaceScalar>),
    Add(AbelianMap<KSpaceScalar>),
    Mul(AbelianMap<KSpaceScalar>),
    FFT(Expr<RealSpaceScalar>),
}

impl KSpaceScalar {
    fn exp(&self) -> Self { KSpaceScalar::Exp(Expr::new(self)) }
    fn log(&self) -> Self { KSpaceScalar::Exp(Expr::new(self)) }
    fn var(name: &str) -> Self { KSpaceScalar::Var(Intern::new(String::from(name))) }
    fn scalar_var(name: &str) -> Self { KSpaceScalar::ScalarVar(Intern::new(String::from(name))) }
    fn ifft(&self) -> RealSpaceScalar { RealSpaceScalar::IFFT(Expr::new(self)) }
}

impl ExprType for KSpaceScalar {
    fn to_generic(self) -> GenericExpr {
        GenericExpr::KSpaceScalar(Expr::new(&self))
    }

    fn cpp(&self) -> String {
        if !(self.contains_fft().len() > 0) {
            return String::from("Vector temp(Nx*Ny*(int(Nz)/2+1));\nfor (int i = 0; i < Nx * Ny * Nz; i++)\n\ttemp[i] = ") + &self.fake_scalar().cpp() + &"\n";
        }
        match self {
            &KSpaceScalar::FFT(a) =>
                match a.inner.deref() {
                    &RealSpaceScalar::Var(s) =>
                        String::from("fft(Nx, Ny, Nz, dV, ") + s.deref() + &")",
                    _ =>
                        String::from("fft(Nx, Ny, Nz, dV, temp)"),
                }
            &KSpaceScalar::Var(s) | &KSpaceScalar::ScalarVar(s) =>
                (*s).clone(),
            &KSpaceScalar::Exp(a) | &KSpaceScalar::Log(a) =>
                a.cpp(),
            &KSpaceScalar::Add(ref m) => {
                let pcoeff = |&(ref x, ref c): &(String, f64)| -> String {
                    if x == "1" {
                        c.to_string()
                    } else if *c == 1.0 {
                        x.clone()
                    } else {
                        c.to_string() + &" * " + &x
                    }
                };
                let ncoeff = |&(ref x, ref c): &(String, f64)| -> String {
                    if x == "1" {
                        c.abs().to_string()
                    } else if *c == -1.0 {
                        x.clone()
                    } else {
                        c.abs().to_string() + &" * " + &x
                    }
                };
                let (p, n) = m.split_cpp_sort();
                match (p.len(), n.len()) {
                    (0, 0) =>
                        String::from("0"),
                    (_, 0) =>
                        p.iter().map(pcoeff).collect::<Vec<String>>().join(" + "),
                    (0, _) =>
                        String::from("-")
                            + &n.iter().map(ncoeff).collect::<Vec<String>>().join(" + "),
                    (_, _) =>
                        p.iter().map(pcoeff).collect::<Vec<String>>().join(" + ")
                            + &" - "
                            + &n.iter().map(ncoeff).collect::<Vec<String>>().join(" + "),
                }
            },
            &KSpaceScalar::Mul(ref m) => {
                let ref power = |&(ref x, ref p): &(String, f64)| -> String {
                    if x == "1" || p.abs() == 1.0 {
                        x.clone()
                    } else if p.abs() == 2.0 {
                        x.clone() + &" * " + &x
                    } else {
                        String::from("pow(") + &x + &", " + &p.abs().to_string() + &")"
                    }
                };
                let (n, d) = m.split_cpp_sort();
                match (n.len(), d.len()) {
                    (0, 0) =>
                        String::from("1"),
                    (_, 0) =>
                        n.iter().map(power).collect::<Vec<String>>().join(" * "),
                    (0, _) =>
                        String::from("1 / (")
                            + &d.iter().map(power).collect::<Vec<String>>().join(" * ")
                            + &")",
                    (_, _) =>
                        n.iter().map(power).collect::<Vec<String>>().join(" * ")
                            + &" / ("
                            + &d.iter().map(power).collect::<Vec<String>>().join(" * ")
                            + &")",
                }
            },
        }
    }

    fn contains_fft(&self) -> Vec<Expr<RealSpaceScalar>> {
        match self {
            &KSpaceScalar::Var(_) | &KSpaceScalar::ScalarVar(_) =>
                Vec::new(),
            &KSpaceScalar::Exp(a) | &KSpaceScalar::Log(a) =>
                a.inner.deref().contains_fft(),
            &KSpaceScalar::FFT(a) =>
                a.inner.deref().contains_fft(),
            &KSpaceScalar::Add(ref m) | &KSpaceScalar::Mul(ref m) =>
                m.into_iter().flat_map(|(k, _)| k.inner.deref().contains_fft()).collect(),
        }
    }

    fn substitute<S: ExprType>(&self, old: Expr<S>, new: Expr<S>) -> Expr<Self> {
        unimplemented!()
    }
    fn map_leaves(x: &Expr<Self>, f: impl Fn(&Expr<Self>) -> Expr<Self>) -> Expr<Self> {
        match x.inner.deref() {
            &KSpaceScalar::Var(_) =>
                f(x),
            &KSpaceScalar::ScalarVar(_) =>
                f(x),
            &KSpaceScalar::Exp(a) =>
                Expr::new(&KSpaceScalar::Exp(f(&a))),
            &KSpaceScalar::Log(a) =>
                Expr::new(&KSpaceScalar::Log(f(&a))),
            &KSpaceScalar::FFT(_) =>
                f(x),
            &KSpaceScalar::Add(ref m) =>
                Expr::new(&KSpaceScalar::Add(AbelianMap::from_iter(m.into_iter().map(|(k, &v)| (f(&k), v))))),
            &KSpaceScalar::Mul(ref m) =>
                Expr::new(&KSpaceScalar::Mul(AbelianMap::from_iter(m.into_iter().map(|(k, &v)| (f(&k), v))))),
        }
    }
}

impl From<Scalar> for RealSpaceScalar {
    fn from(s: Scalar) -> Self {
        match s {
            Scalar::Var(name) =>
                RealSpaceScalar::ScalarVar(name),
            Scalar::Integrate(s, a) =>
                panic!("Tried to convert a Scalar expression involving integration into a RealSpaceScalar"),
            Scalar::Exp(a) =>
                RealSpaceScalar::Exp(Expr::new(&a.inner.deref().clone().into())),
            Scalar::Log(a) =>
                RealSpaceScalar::Log(Expr::new(&a.inner.deref().clone().into())),
            Scalar::Add(m) =>
                RealSpaceScalar::Add(
                    m.iter()
                     .map(|(k, &v)| (Expr::new(&k.inner.deref().clone().into()), v))
                     .collect()),
            Scalar::Mul(m) =>
                RealSpaceScalar::Mul(
                    m.iter()
                     .map(|(k, &v)| (Expr::new(&k.inner.deref().clone().into()), v))
                     .collect()),
        }
    }
}

trait FakeScalar {
    fn fake_scalar(&self) -> Scalar; // FIXME consider -> Result<Scalar, Expr<Self>>?
}

impl FakeScalar for RealSpaceScalar {
    fn fake_scalar(&self) -> Scalar {
        match self {
            &RealSpaceScalar::Var(ref name) =>
                Scalar::Var(Intern::new(String::new() + name.deref() + &"[i]")),
            &RealSpaceScalar::ScalarVar(ref name) =>
                Scalar::Var(name.clone()),
            &RealSpaceScalar::Exp(ref a) =>
                Scalar::Exp(Expr::new(&a.inner.deref().fake_scalar())),
            &RealSpaceScalar::Log(ref a) =>
                Scalar::Log(Expr::new(&a.inner.deref().fake_scalar())),
            &RealSpaceScalar::Add(ref m) =>
                Scalar::Add(
                    m.iter()
                     .map(|(k, &v)| (Expr::new(&k.inner.deref().fake_scalar()), v))
                     .collect()),
            &RealSpaceScalar::Mul(ref m) =>
                Scalar::Mul(
                    m.iter()
                     .map(|(k, &v)| (Expr::new(&k.inner.deref().fake_scalar()), v))
                     .collect()),
            &RealSpaceScalar::IFFT(_) =>
                panic!(),
        }
    }
}

impl FakeScalar for KSpaceScalar {
    fn fake_scalar(&self) -> Scalar {
        match self {
            &KSpaceScalar::Var(ref name) =>
                Scalar::Var(Intern::new(String::new() + name.deref() + &"[i]")),
            &KSpaceScalar::ScalarVar(ref name) =>
                Scalar::Var(name.clone()),
            &KSpaceScalar::Exp(ref a) =>
                Scalar::Exp(Expr::new(&a.inner.deref().fake_scalar())),
            &KSpaceScalar::Log(ref a) =>
                Scalar::Log(Expr::new(&a.inner.deref().fake_scalar())),
            &KSpaceScalar::Add(ref m) =>
                Scalar::Add(
                    m.iter()
                     .map(|(k, &v)| (Expr::new(&k.inner.deref().fake_scalar()), v))
                     .collect()),
            &KSpaceScalar::Mul(ref m) =>
                Scalar::Mul(
                    m.iter()
                     .map(|(k, &v)| (Expr::new(&k.inner.deref().fake_scalar()), v))
                     .collect()),
            &KSpaceScalar::FFT(_) =>
                panic!("It is invalid to make fake_scalar with an FFT!"),
        }
    }
}

#[derive(Clone)]
pub struct AbelianMap<T: ExprType> {
    inner: Map64<Expr<T>, f64>,
}

impl<T: ExprType> AbelianMap<T> {
    fn new() -> Self {
        Self { inner: Map64::new(), }
    }

    fn iter(&self) -> <&Self as IntoIterator>::IntoIter {
        self.into_iter()
    }

    fn len(&self) -> usize {
        self.inner.len()
    }

    fn insert(&mut self, k: Expr<T>, v: f64) {
        let v = self.inner.get(&k).unwrap_or(&0.0) + v;
        if v == 0.0 {
            self.inner.remove(&k);
        } else {
            self.inner.insert(k, v);
        }
    }

    fn union(&mut self, other: &Self) {
        for (k, &v) in other {
            self.insert(k, v);
        }
    }

    fn split_cpp_sort(&self) -> (Vec<(String, f64)>, Vec<(String, f64)>) {
        let (mut p, mut n): (Vec<(String, f64)>, Vec<(String, f64)>)
            = self.iter()
                  .map(|(k, &v)| (k.cpp(), v))
                  .partition(|&(_, v)| v > 0.0);
        let ref by_key = |&(ref p, _): &(String, f64), &(ref q, _): &(String, f64)| {
            p.cmp(&q)
        };
        p.sort_by(by_key);
        n.sort_by(by_key);
        (p, n)
    }
}

impl<T: ExprType> Debug for AbelianMap<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        let mut res = write!(f, "AbelianMap [ ");
        for term in self {
            res = res.and(write!(f, "{:?}, ", term));
        }
        res.and(write!(f, "] "))
    }
}

impl<'a, T: ExprType> IntoIterator for &'a AbelianMap<T> {
    type Item = (Expr<T>, &'a f64);
    type IntoIter = Map64Iter<'a, Expr<T>, f64>;

    fn into_iter(self) -> Self::IntoIter {
        self.inner.iter()
    }
}

// May not be needed.
//
// impl<'a, T: ExprType> FromIterator<(Expr<T>, &'a f64)> for AbelianMap<T> {
//     fn from_iter<I: IntoIterator<Item = (Expr<T>, &'a f64)>>(iter: I) -> Self {
//         let mut map = AbelianMap::new();
//         for (k, &v) in iter {
//             map.insert(k, v);
//         }
//         map
//     }
// }

impl<'a, T: ExprType> FromIterator<(Expr<T>, f64)> for AbelianMap<T> {
    fn from_iter<I: IntoIterator<Item = (Expr<T>, f64)>>(iter: I) -> Self {
        let mut map = AbelianMap::new();
        for (k, v) in iter {
            map.insert(k, v);
        }
        map
    }
}

// May not be needed.
//
// impl<'a, T: ExprType> FromIterator<Expr<T>> for AbelianMap<T> {
//     fn from_iter<I: IntoIterator<Item = Expr<T>>>(iter: I) -> Self {
//         let mut map = AbelianMap::new();
//         for k in iter {
//             map.insert(k, 1.0);
//         }
//         map
//     }
// }

impl<'a, T: ExprType> FromIterator<T> for AbelianMap<T> {
    fn from_iter<I: IntoIterator<Item = T>>(iter: I) -> Self {
        let mut map = AbelianMap::new();
        for k in iter {
            map.insert(Expr::new(&k), 1.0);
        }
        map
    }
}

impl<T: ExprType> Hash for AbelianMap<T> {
    fn hash<H: std::hash::Hasher>(&self, hasher: &mut H) {
        let mut terms: Vec<_>
            = self.iter()
                  .map(|(k, &v)| (k.inner.to_u64(), v as u64))
                  .collect();
        terms.sort();
        for (k, v) in terms {
            k.hash(hasher);
            v.hash(hasher);
        }
    }
}

impl<T: ExprType> PartialEq for AbelianMap<T> {
    fn eq(&self, other: &Self) -> bool {
        let mut lhs: Vec<_>
            = self.iter()
                  .map(|(k, &v)| (k.inner.to_u64(), v as u64))
                  .collect();
        let mut rhs: Vec<_>
            = other.iter()
                   .map(|(k, &v)| (k.inner.to_u64(), v as u64))
                   .collect();
        lhs.sort();
        rhs.sort();
        lhs == rhs
    }
}

impl<T: ExprType> Eq for AbelianMap<T> {}

impl Expr<KSpaceScalar> {
    fn ifft(&self) -> Expr<RealSpaceScalar> {
        Expr::new(&self.inner.ifft())
    }

    fn var<T: Into<String>>(s: T) -> Self {
        Expr::new(&KSpaceScalar::var(&s.into()))
    }
}

impl Expr<RealSpaceScalar> {
    fn fft(&self) -> Expr<KSpaceScalar> {
        Expr::new(&self.inner.fft())
    }

    fn var<T: Into<String>>(s: T) -> Self {
        Expr::new(&RealSpaceScalar::var(&s.into()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn abelian() {
        let t = vec![Scalar::var("x"), Scalar::var("x"), Scalar::var("y"), Scalar::var("z")];
        let s: AbelianMap<Scalar> = t.into_iter().collect();
        assert_eq!(s, s);
        assert_eq!(s, s.iter().map(|(k, &v)| (k, v)).collect());
        assert!(s != vec![Scalar::var("x"), Scalar::var("y"), Scalar::var("z")].into_iter().collect());
    }

    #[test]
    fn arith() {
        let a = Expr::new(&Scalar::var("a"));
        let b = Expr::new(&Scalar::var("b"));

        assert_eq!(a, a);
        assert!(a != b);

        assert_eq!(a + 0, a);
        assert_eq!(a + a, a + a);
        assert_eq!(a + b, a + b);
        assert_eq!(a + b, b + a);
        assert_eq!(a + a - a, a);
        assert_eq!(a - a, 0);
        assert_eq!(a + a - a - a, 0);

        assert_eq!(a * 1, a);
        assert_eq!(a * a, a * a);
        assert_eq!(a * b, a * b);
        assert_eq!(a * b, b * a);
        assert_eq!(a * a / a, a);
        assert_eq!(a / a, 1);
        assert_eq!(a * a / a / a, 1);
    }

    #[test]
    fn realspace() {
        let a: Expr<RealSpaceScalar> = <Expr<RealSpaceScalar>>::new(&RealSpaceScalar::var("a"));
        let s: Expr<Scalar> = <Expr<Scalar>>::new(&Scalar::var("s"));
        let rs_s: Expr<RealSpaceScalar> =
            <Expr<RealSpaceScalar>>::new(&RealSpaceScalar::scalar_var("s"));

        assert_eq!(a * rs_s, a * rs_s);

        // FIXME the following is broken:
        // assert_eq!(a * s, a * rs_s);
    }

    #[test]
    fn cpp() {
        let a = Expr::new(&Scalar::var("a"));
        let b = Expr::new(&Scalar::var("b"));
        let c = Expr::new(&Scalar::var("c"));

        assert_eq!((c + b + a).cpp(), "a + b + c");
        assert_eq!((c * b * a).cpp(), "a * b * c");
        assert_eq!((a / c / b).cpp(), "a / (b * c)");
    }

    #[test]
    fn fourier() {
        let k = Expr::new(&KSpaceScalar::var("k"));
        assert_eq!(k.ifft().cpp(), "ifft(Nx, Ny, Nz, dV, k)");
        let k2 = Expr::new(&KSpaceScalar::var("k2"));
        assert_eq!((k+k2).ifft().cpp(), "ifft(Nx, Ny, Nz, dV, temp)");
        assert_eq!(Expr::new(&RealSpaceScalar::var("r").fft()).cpp(), "fft(Nx, Ny, Nz, dV, r)");
    }

    #[test]
    fn replacer() {
        let a = Expr::new(&Scalar::var("a"));
        let b = Expr::new(&Scalar::var("b"));
        let x = Expr::new(&Scalar::var("x"));
        let y = Expr::new(&Scalar::var("y"));
        assert_eq!((x + y).cpp(), Scalar::map_leaves(&(a + b), |&x| {
            match x.inner.deref() {
                &Scalar::Var(s) => {
                    if s.deref() == "a" {
                        Expr::new(&Scalar::var("x"))
                    } else {
                        Expr::new(&Scalar::var("y"))
                    }
                },
                _ => x,
            }
        }).cpp());
    }
}

// CAN WE MAKE A MAP FUNCTION?
//fn<T: ExprType> expr_map_scalar(Expr<T>, impl Fn(Expr<Scalar>) -> Expr<Scalar>) -> Expr<T> {
//}
// WANT: substitute, has_subexpr, has_fft, has_ifft, has_integrate, find_set_of_variables?

/// Maybe the following should not be a trait? impl for Expr<ExprType>?
pub trait ToStmts: ExprType {
    fn to_stmts(&self) -> (Vec<Stmt>, Expr<Self>) {
        if Expr::new(self).inner.deref().contains_fft().len() > 0 {
            ()
        }
        (Vec::new(), Expr::new(self))
    }
}

impl ToStmts for Scalar {
}

impl ToStmts for KSpaceScalar {
}

#[test]
fn test_stmts() {
    let x = Scalar::var("x");
    assert_eq!(x.to_stmts().0.len(), 0);
}
