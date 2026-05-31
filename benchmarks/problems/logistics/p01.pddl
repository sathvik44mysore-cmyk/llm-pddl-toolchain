(define (problem logistics-1-pkg)
  (:domain logistics)
  (:objects
    pkg1          - package
    truck1        - truck
    plane1        - airplane
    loc1 loc2     - location
    apt1          - airport
    city1         - city
  )
  (:init
    (in-city loc1 city1)
    (in-city loc2 city1)
    (in-city apt1 city1)
    (at truck1 loc1)
    (at plane1 apt1)
    (at pkg1   loc1)
  )
  (:goal
    (at pkg1 loc2)
  )
)
