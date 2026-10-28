(ns feedback-fixture
  "Native Jolt emission of the actual app shader and a deterministic fixture."
  (:require [feedback.model :as model]
            [feedback.visuals :as visuals]
            [clojure.string :as str]))

(defn -main [output]
  (let [state (nth (iterate #(model/advance % model/tick)
                                  (assoc (model/initial-state) :tail 48)) 65)
        effect (visuals/effect state)
        uniforms (:uniforms effect)
        entries (sort-by (comp str key) uniforms)]
    (spit output
      (str "// Generated from feedback.model and feedback.visuals; do not edit.\n"
           "static const char* feedback_hook = R\"SHADER(" (:fragment-hook effect) ")SHADER\";\n"
           "static const char* feedback_declarations = R\"SHADER("
           (str/join "\n" (for [[name {:keys [type]}] entries]
                             (str "uniform " (if (= type :mat3) "mat3" "float")
                                  " u_" (clojure.core/name name) ";")))
           ")SHADER\";\nstatic SSGLUniform feedback_uniforms[] = {\n"
           (str/join ",\n"
             (for [[name {:keys [type value]}] entries]
               (str "{\"u_" (clojure.core/name name) "\", "
                    (if (= type :mat3) "16, 9" "0, 1") ", {"
                    (str/join "," (map #(str (double %) "f")
                                       (if (= type :mat3) value [value]))) "}, {}, {}}")))
           "\n};\n"))))
