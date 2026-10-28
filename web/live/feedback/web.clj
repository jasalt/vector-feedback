(ns feedback.web
  "Experimental owner-thread Jolt model driving the real Slipstream WebGL scene."
  (:require [jolt.ffi :as ffi]
            [feedback.model :as model]
            [feedback.visuals :as visuals]
            [clojure.string :as str]))

(ffi/defcfn input! "web_scene_input" [:pointer] :int32)
(ffi/defcfn submit! "web_scene_submit" [:pointer] :int32)
(ffi/defcfn set-tail! "web_scene_set_tail" [:int32 :pointer :pointer :pointer] :int32)
(defonce active-tail (atom 48))
(defonce state (atom (model/initial-state)))
;; Buffers live for the module lifetime; C borrows only for each call.
(defonce input-buffer (ffi/alloc (* 11 4)))
(defonce payload (ffi/alloc (* (+ 10 (* 9 model/max-depth)) 4)))
(defn checked [result]
  (when-not (zero? result) (throw (ex-info "Slipstream web adapter failed" {:code result}))))
(defn frame! []
  (checked (input! input-buffer))
  (let [v (mapv #(double (ffi/read input-buffer :float (* 4 %))) (range 11))
        input {:mouse [(nth v 0) (nth v 1)] :scroll-y (nth v 2)
               :left (pos? (nth v 3)) :right (pos? (nth v 4)) :middle (pos? (nth v 5))
               :space (pos? (nth v 6)) :r (pos? (nth v 7))
               :increase-tail (pos? (nth v 9)) :decrease-tail (pos? (nth v 10))}
        s (swap! state #(model/advance (model/update-input % input) (nth v 8)))
        effect (visuals/effect s)
        ordered (sort-by (comp str key) (:uniforms effect))
        values (vec (concat
                      (mapcat (fn [[_ {:keys [type value]}]]
                                (if (= type :mat3) value [value])) ordered)
                      [(if (:paused s) 1.0 0.0) (:time s)
                       (get-in s [:camera :zoom]) (get-in s [:camera :pan-x])
                       (get-in s [:camera :pan-y]) (get-in s [:camera :yaw])
                       (get-in s [:camera :pitch]) (get-in s [:camera :roll])] ))]
    (when-not (= (+ 10 (* 9 (:tail s))) (count values))
      (throw (ex-info "Invalid web effect payload length" {})))
    (doseq [[i value] (map-indexed vector values)]
      (ffi/write payload :float value (* i 4)))
    (when-not (= @active-tail (:tail s))
      (let [hook (ffi/string->ptr (:fragment-hook effect))
            declarations (ffi/string->ptr
                           (str/join "\n"
                             (for [[name {:keys [type]}] ordered]
                               (str "uniform " (if (= type :mat3) "mat3" "float")
                                    " u_" (clojure.core/name name) ";"))))]
        (try
          (checked (set-tail! (:tail s) hook declarations payload))
          (reset! active-tail (:tail s))
          (finally (ffi/free hook) (ffi/free declarations)))))
    (checked (submit! payload))))
(defn -main [& args]
  (println "SLIPSTREAM-JOLT-LIVE-BOOT"))
