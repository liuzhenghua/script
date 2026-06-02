# ---- Build Stage ----
FROM eclipse-temurin:21-jdk-alpine AS build

WORKDIR /app

COPY mvnw .
COPY .mvn .mvn

COPY pom.xml .
COPY src ./src

RUN --mount=type=cache,id=maven_cache,target=/root/.m2,sharing=locked \
    chmod +x mvnw && \
    ./mvnw package -DskipTests -B

# ---- Runtime Stage ----
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

COPY --from=build /app/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]