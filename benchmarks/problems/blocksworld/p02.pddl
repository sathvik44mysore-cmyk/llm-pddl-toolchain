(define (problem bw-4-blocks)
  (:domain blocksworld)
  (:objects a b c d - block)
  (:init
    (ontable a) (clear a)
    (ontable b) (clear b)
    (ontable c) (clear c)
    (ontable d) (clear d)
    (handempty)
  )
  (:goal
    (and (on a b) (on b c) (on c d) (ontable d))
  )
)
