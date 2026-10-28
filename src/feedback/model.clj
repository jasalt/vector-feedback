(ns feedback.model)

;; Row-major homogeneous matrices. Coordinates use an undistorted Y-up plane.
(def identity-matrix [1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0])
(def depth 48)
;; Keep mat3 uniforms within OpenGL 3.3's minimum fragment-uniform budget.
(def min-depth 8)
(def max-depth 78)
(def tick (/ 1.0 60.0))
(def defaults {:pan-x 0.008 :pan-y 0.0 :zoom 0.965
               :roll 0.025 :yaw 0.012 :pitch -0.008 :decay 0.955})
(defn clamp [x lo hi] (max lo (min hi x)))
(defn multiply [a b]
  (vec (for [row (range 3) col (range 3)]
         (reduce + (for [k (range 3)] (* (nth a (+ (* row 3) k))
                                         (nth b (+ (* k 3) col))))))))
(defn project [m [x y]]
  (let [[a b c d e f g h i] m w (+ (* g x) (* h y) i)]
    (when (> (Math/abs (double w)) 1.0e-9)
      [(/ (+ (* a x) (* b y) c) w) (/ (+ (* d x) (* e y) f) w)])))
(defn inverse [m]
  (let [[a b c d e f g h i] m
        cof [(- (* e i) (* f h)) (- (* c h) (* b i)) (- (* b f) (* c e))
             (- (* f g) (* d i)) (- (* a i) (* c g)) (- (* c d) (* a f))
             (- (* d h) (* e g)) (- (* b g) (* a h)) (- (* a e) (* b d))]
        det (+ (* a (nth cof 0)) (* b (nth cof 3)) (* c (nth cof 6)))]
    (when (> (Math/abs (double det)) 1.0e-12)
      (mapv #(/ % det) cof))))
(defn camera-matrix [{:keys [pan-x pan-y zoom roll yaw pitch]}]
  ;; Rz * Ry * Rx, then pinhole projection at focal distance 2.5.
  (let [cx (Math/cos pitch) sx (Math/sin pitch)
        cy (Math/cos yaw) sy (Math/sin yaw)
        cz (Math/cos roll) sz (Math/sin roll)
        rotation [(* cz cy) (- (* cz sy sx) (* sz cx)) 0.0
                  (* sz cy) (+ (* sz sy sx) (* cz cx)) 0.0
                  (/ (- sy) 2.5) (/ (* cy sx) 2.5) 1.0]
        placement [zoom 0.0 pan-x 0.0 zoom pan-y 0.0 0.0 1.0]]
    (multiply placement rotation)))
(defn initial-state []
  {:camera defaults :tail depth :history [] :pending 0.0 :time 0.0 :paused false :input {}})
(defn feedback-step
  ([history camera] (feedback-step history camera depth))
  ([history camera tail]
   (let [h (camera-matrix camera)]
     (into [identity-matrix]
           (take (dec tail) (map #(multiply h %) history))))))
(defn resize-tail [state delta]
  (let [tail (clamp (+ (:tail state) delta) min-depth max-depth)]
    (assoc state :tail tail :history (vec (take tail (:history state))))))
(defn advance [state dt]
  (if (:paused state)
    state
    (let [elapsed (+ (:pending state) (clamp dt 0.0 0.1))
          steps (long (/ elapsed tick))]
      (assoc state :pending (- elapsed (* steps tick))
             :time (+ (:time state) (* steps tick))
             :history (nth (iterate #(feedback-step % (:camera state) (:tail state)) (:history state)) steps)))))
(defn update-input [state input]
  (let [previous (:input state)
        [x y] (:mouse input [0.0 0.0])
        [px py] (:mouse previous [x y])
        dx (- x px) dy (- y py)
        rising? (fn [k] (and (get input k) (not (get previous k))))]
    (if (rising? :r)
      (assoc (initial-state) :input input)
      (-> state
          (resize-tail (+ (if (rising? :increase-tail) 10 0)
                          (if (rising? :decrease-tail) -10 0)))
          (update :paused #(if (rising? :space) (not %) %))
          (update :camera
                  (fn [c]
                    (let [drag? (fn [k] (and (get input k) (get previous k)))]
                      (cond-> (update c :zoom #(clamp (+ % (* 0.008 (:scroll-y input 0.0))) 0.8 1.08))
                        (drag? :left) (update :pan-x #(clamp (+ % (* dx 0.12)) -0.15 0.15))
                        (drag? :left) (update :pan-y #(clamp (+ % (* dy 0.12)) -0.15 0.15))
                        (drag? :right) (update :yaw #(clamp (+ % (* dx 0.3)) -0.35 0.35))
                        (drag? :right) (update :pitch #(clamp (- % (* dy 0.3)) -0.35 0.35))
                        (drag? :middle) (update :roll #(clamp (+ % (* dx 0.3)) -0.3 0.3))))))
          (assoc :input input)))))
