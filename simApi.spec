%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name: simApi
Version: 1.0.0
Release: 2%{?dist}
Summary: vEOS extension to serve custom eAPI responses

Group: Development/Libraries
URL: http://eos.arista.com
Source0: %{name}-%{version}.tar.gz

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
vEOS extension enables users to retriece custom eAPI responses from the switch.

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,eosadmin,-)
%{python_sitelib}/rphm*
%{_bindir}/simAPI
%config(noreplace) /persist/sys/simApi.conf

%changelog
* Tue Sep 23 2014 Andrei Dvornic <andrei@arista.com> - 1.0.0-0
- Initial release