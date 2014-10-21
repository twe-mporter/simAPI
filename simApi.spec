%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name: simApi
Version: PLEASE_LEAVE_BLANK
Release: 2%{?dist}
Summary: vEOS extension to serve custom eAPI responses
License: BSD-3

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
%{python_sitelib}/SimApi.py*
%{python_sitelib}/simApi-1.0.0-py2.7.egg-info/*
%{_sysconfdir}/nginx/external_conf/simApi.conf
%{_sysconfdir}/uwsgi/simApi.ini
%config(noreplace) /persist/sys/simApi.json

%changelog
* Tue Sep 23 2014 Andrei Dvornic <andrei@arista.com> - 1.0.0-1
- Initial release
