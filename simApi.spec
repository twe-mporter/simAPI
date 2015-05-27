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

%post
sudo service nginx restart
sudo /usr/bin/immortalize --daemonize /usr/bin/uwsgi --ini /etc/uwsgi/simApi.ini

%postun
sudo service nginx restart
rm -rf /persist/sys/simAPI

%files
%defattr(-,root,eosadmin,-)
%{python_sitelib}/SimApi.pyc
%{python_sitelib}/simApi-%{version}-py2.7.egg-info/*
%{_sysconfdir}/nginx/external_conf/simApi.conf
%{_sysconfdir}/uwsgi/simApi.ini
%config(noreplace) /persist/sys/simAPI/simApi.json
%config /persist/sys/simAPI/plugins/show_port-channel
%config /persist/sys/simAPI/plugins/replace_strings
%config /persist/sys/simAPI/plugins/ibm
%exclude %{python_sitelib}/SimApi.py
%exclude %{python_sitelib}/SimApi.pyo
