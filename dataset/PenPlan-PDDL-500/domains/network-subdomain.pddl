(define (domain pentest-network)
  (:requirements :strips :typing :conditional-effects)

  (:types
    asset tool credential data - object
    network-asset system-asset service-asset - asset
    attack-tool defense-tool - tool
    vulnerability protocol os-type patch-level privesc-type - object
    version config-type action segment vlan rule port software - object
  )

  (:predicates
    ;; Core connectivity predicates
    (connected ?from ?to - asset)
    (allowed ?proto - protocol ?from ?to - asset)
    (isolated ?asset - asset)
    (discovered ?asset - asset)
    (user-access ?system - system-asset)
    (service-running ?service - service-asset)
    (has-vuln ?service - service-asset ?cve - vulnerability)
    (detected ?activity - action ?defense - defense-tool)
    (evaded ?activity - action ?defense - defense-tool)

    ;; Network topology and access control
    (network-segment ?asset - asset ?segment - segment)
    (firewall-rule ?rule - rule ?from ?to - segment)
    (vlan-isolation ?vlan1 ?vlan2 - vlan)
    (routing-table ?router - asset ?dest - segment ?next-hop - asset)
  )

  (:action network-scan
    :parameters (?attacker - asset ?target - network-asset ?tool - attack-tool)
    :precondition (and (connected ?attacker ?target)
                       (not (isolated ?target)))
    :effect (discovered ?target)
  )

  (:action exploit-public-facing-app
    :parameters (?attacker - asset ?target - service-asset ?vuln - vulnerability)
    :precondition (and (connected ?attacker ?target)
                       (has-vuln ?target ?vuln)
                       (service-running ?target))
    :effect (and (user-access ?target)
                 (when (not (evaded exploit-public-facing-app web-application-firewall))
                       (detected exploit-public-facing-app web-application-firewall)))
  )
)