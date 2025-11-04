(define (domain pentest-service)
  (:requirements :strips :typing :conditional-effects)

  (:types
    asset tool credential data - object
    network-asset system-asset service-asset - asset
    attack-tool defense-tool - tool
    vulnerability protocol os-type patch-level privesc-type - object
    version config-type action segment vlan rule port software - object
  )

  (:predicates
    ;; Core predicates
    (connected ?from ?to - asset)
    (user-access ?system - system-asset)
    (admin-access ?system - system-asset)
    (service-version ?service - service-asset ?version - version)
    (has-vuln ?service - service-asset ?cve - vulnerability)
    (service-running ?service - service-asset)
    (detected ?activity - action ?defense - defense-tool)
    (evaded ?activity - action ?defense - defense-tool)
    (exfiltrated ?data - data)

    ;; Service specific predicates
    (service-port ?service - service-asset ?port - port)
    (authentication-required ?service - service-asset)
    (ssl-enabled ?service - service-asset)
  )

  (:action exploit-cve-2021-41773
    :parameters (?attacker - asset ?apache - service-asset)
    :precondition (and (service-version ?apache apache-2-4-41)
                       (has-vuln ?apache cve-2021-41773)
                       (service-running ?apache))
    :effect (and (user-access ?apache)
                 (when (not (evaded exploit-cve-2021-41773 web-application-firewall))
                       (detected exploit-cve-2021-41773 web-application-firewall)))
  )

  (:action exploit-cve-2021-42013
    :parameters (?attacker - asset ?apache - service-asset)
    :precondition (and (service-version ?apache apache-2-4-41)
                       (has-vuln ?apache cve-2021-42013)
                       (service-running ?apache))
    :effect (and (user-access ?apache)
                 (when (not (evaded exploit-cve-2021-42013 web-application-firewall))
                       (detected exploit-cve-2021-42013 web-application-firewall)))
  )

  (:action use-valid-accounts
    :parameters (?attacker - asset ?target - system-asset ?data - data)
    :precondition (and (admin-access ?target)
                       (connected ?target ?data))
    :effect (exfiltrated ?data)
  )
)