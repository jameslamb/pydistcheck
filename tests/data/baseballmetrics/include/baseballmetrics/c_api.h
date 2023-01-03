#ifndef BASEBALLMETRICS_C_API_H_
#define BASEBALLMETRICS_C_API_H_

/** exporting symbols **/

#ifdef __cplusplus
    #define BASEBALLMETRICS_EXTERN_C extern "C"
#else
    #define BASEBALLMETRICS_EXTERN_C
#endif

#ifdef _MSC_VER
    #define BASEBALLMETRICS_C_EXPORT BASEBALLMETRICS_EXTERN_C __declspec(dllexport)
#else
    #define BASEBALLMETRICS_C_EXPORT BASEBALLMETRICS_EXTERN_C
#endif

BASEBALLMETRICS_C_EXPORT void BattingAverage(
    const int hits,
    const int at_bats,
    double* ret
);

#endif /** BASEBALLMETRICS_EXPORT_H_ **/
