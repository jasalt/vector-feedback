(ns feedback.test-runner
  (:require [clojure.test :refer [deftest is run-tests]]
            [feedback.model :as m]
            [feedback.visuals :as v]))
(defn near? [a b] (< (Math/abs (double (- a b))) 1.0e-8))
(deftest camera-and-inverse
  (let [c (assoc m/defaults :yaw 0.2 :pitch -0.15)
        h (m/camera-matrix c)
        inv (m/inverse h)]
    (is (every? true? (map near? m/identity-matrix (m/multiply h inv)))))
  (is (= [2.0 3.0] (m/project m/identity-matrix [2.0 3.0])))
  (is (nil? (m/inverse (vec (repeat 9 0.0)))))
  (is (every? true? (map near? m/identity-matrix
                              (m/camera-matrix (assoc m/defaults :pan-x 0.0 :pan-y 0.0
                                                     :zoom 1.0 :yaw 0.0 :pitch 0.0 :roll 0.0))))))
(deftest temporal-feedback
  (let [s (nth (iterate #(m/advance % m/tick) (m/initial-state)) 100)]
    (is (= m/depth (count (:history s))))
    (is (= m/identity-matrix (first (:history s))))
    (is (= (m/camera-matrix m/defaults) (second (:history s))))
    (is (= (:history s) (:history (m/advance (assoc s :paused true) 10.0))))
    (is (= 1 (count (:history (m/advance (m/initial-state) m/tick)))))))
(deftest input-edges-and-limits
  (let [s (m/update-input (m/initial-state) {:space true})]
    (is (:paused s))
    (is (:paused (m/update-input s {:space true})))
    (is (not (:paused (-> s (m/update-input {:space false}) (m/update-input {:space true}))))))
  (is (= 1.08 (get-in (m/update-input (m/initial-state) {:scroll-y 10000}) [:camera :zoom])))
  (is (= m/defaults (:camera (m/update-input (assoc (m/initial-state) :camera {}) {:r true})))))
(deftest history-retains-earlier-camera-movement
  (let [a (assoc m/defaults :pan-x 0.1)
        b (assoc m/defaults :yaw 0.1)
        history (-> [] (m/feedback-step a) (m/feedback-step a) (m/feedback-step b))]
    (is (= (m/multiply (m/camera-matrix b) (m/camera-matrix a)) (nth history 2)))))
(deftest drag-is-relative-and-does-not-jump-on-press
  (let [s (m/initial-state)
        pressed (m/update-input s {:left true :mouse [1.0 1.0]})
        moved (m/update-input pressed {:left true :mouse [1.2 1.1]})]
    (is (= (:camera s) (:camera pressed)))
    (is (near? 0.032 (get-in moved [:camera :pan-x])))
    (is (near? 0.012 (get-in moved [:camera :pan-y])))))
(deftest uniforms-are-stable-and-column-major
  (is (= [1 4 7 2 5 8 3 6 9] (v/column-major [1 2 3 4 5 6 7 8 9])))
  (is (= (+ 2 m/depth) (count (:uniforms (v/effect (m/initial-state))))))
  (is (= :mat3 (get-in (v/effect (m/initial-state)) [:uniforms :frame0 :type]))))
(defn -main [& _]
  (let [{:keys [fail error]} (run-tests 'feedback.test-runner)]
    (when (pos? (+ fail error)) (System/exit 1))))
