(define (domain pentest-system)
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
    (os ?system - system-asset ?type - os-type)
    (persisted ?system - system-asset)
    (detected ?activity - action ?defense - defense-tool)
    (evaded ?activity - action ?defense - defense-tool)

    ;; System specific predicates
    (kernel-version ?system - system-asset ?version - version)
    (installed-software ?system - system-asset ?software - software)
  )

  (:action wmi-execution
    :parameters (?attacker - asset ?target - system-asset)
    :precondition (and (user-access ?target)
                       (os ?target windows)
                       (not (detected wmi-execution crowdstrike-falcon)))
    :effect (admin-access ?target)
  )

  (:action create-scheduled-task
    :parameters (?attacker - asset ?target - system-asset)
    :precondition (and (admin-access ?target)
                       (os ?target windows))
    :effect (and (persisted ?target)
                 (when (not (evaded create-scheduled-task crowdstrike-falcon))
                       (detected create-scheduled-task crowdstrike-falcon)))
  )

  (:action exploit-client-side-tech
    :parameters (?attacker - asset ?target - system-asset ?defense - defense-tool)
    :precondition (and (user-access ?target)
                       (not (detected exploit-client-side-tech ?defense)))
    :effect (and (admin-access ?target)
                 (when (not (evaded exploit-client-side-tech ?defense))
                       (detected exploit-client-side-tech ?defense)))
  )
)